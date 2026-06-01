"""Tronc commun de la génération de code (couche partagée).

Responsabilités :
  - `build_symbols` : pré-passe qui remplit la table des symboles (types des
    variables globales, fonctions et leurs variables locales).
  - `asm_expression` / `asm_commande` : génération des expressions et commandes
    générales (entiers, opérateurs, if/while/print/affectation) et DISPATCH
    vers les modules de feature selon le type lu dans la table des symboles.
  - `Gen` : petit objet de contexte passé aux modules de feature pour qu'ils
    puissent générer sous-expressions/sous-commandes sans s'importer entre eux.

Ce module importe les 3 modules de feature ; les modules de feature, eux,
n'importent PAS codegen_base (ils reçoivent `gen`). -> pas d'import circulaire.
"""

from __future__ import annotations

from lark import Token, Tree

import codegen_array
import codegen_dict
import codegen_func
from symboltable import FuncInfo, SymbolTable

# ── opérateurs binaires : rax = gauche, rbx = droite ──────────────────────
_ARITH: dict[str, str] = {"+": "add", "-": "sub", "*": "imul"}
_CMP: dict[str, str] = {"<": "setl", ">": "setg", "==": "sete", "!=": "setne"}


class Gen:
    """Contexte de génération partagé, passé aux modules de feature.

    `scope` vaut `None` au niveau du `main` (variables globales) ou bien une
    `FuncInfo` à l'intérieur d'une fonction (variables locales sur la pile).
    """

    def __init__(self, symtab: SymbolTable) -> None:
        self.symtab: SymbolTable = symtab

    def expr(self, ast: Tree, scope: object) -> str:
        return asm_expression(ast, scope, self)

    def cmd(self, ast: Tree, scope: object) -> str:
        return asm_commande(ast, scope, self)

    def new_label(self, prefix: str) -> str:
        return self.symtab.new_label(prefix)


# ── résolution d'adresse d'une variable scalaire entière ──────────────────


def var_operand(name: str, scope: object, gen: Gen) -> str:
    """Opérande mémoire d'une variable entière (`[rbp - d]` ou `[gv_x]`).

    Dans une fonction : seules les variables locales sont accessibles.
    Au niveau global : la variable doit être déclarée et de type "int".
    Lève `NameError`/`TypeError` plutôt que de produire du code faux.
    """
    st: SymbolTable = gen.symtab
    if isinstance(scope, FuncInfo):
        if name in scope.locals:
            return f"[rbp - {scope.offset(name)}]"
        raise NameError(
            f"variable inconnue dans la fonction {scope.name!r} : {name!r}"
        )
    if not st.is_global(name):
        raise NameError(f"variable globale inconnue : {name!r}")
    if st.type_of(name) != "int":
        raise TypeError(f"{name!r} n'est pas un entier scalaire")
    return f"[{st.gv(name)}]"


# ── expressions (résultat dans rax) ───────────────────────────────────────


def asm_expression(ast: Tree, scope: object, gen: Gen) -> str:
    data: str = ast.data
    if data == "variable":
        name: str = _ident(ast.children[0])
        return f"mov rax, {var_operand(name, scope, gen)}\n"
    if data == "entier":
        return f"mov rax, {int(_token(ast.children[0]))}\n"
    if data == "binaire":
        return _asm_binaire(ast, scope, gen)
    if data == "appel_fonction":
        return codegen_func.asm_appel(ast, scope, gen)
    if data == "acces_index":
        return _asm_acces_index(ast, scope, gen)
    if data == "longueur":
        return _asm_longueur(ast, scope, gen)
    if data in ("dict_vide", "dict_literal"):
        raise ValueError(
            "dict()/{...} n'est valide qu'en partie droite d'une affectation"
        )
    raise NotImplementedError(f"expression non gérée : {data!r}")


def _asm_binaire(ast: Tree, scope: object, gen: Gen) -> str:
    left: Tree = _tree(ast.children[0])
    op: str = _token(ast.children[1])
    right: Tree = _tree(ast.children[2])
    # On évalue la droite, on l'empile, puis la gauche -> rax=gauche, rbx=droite
    base: str = (
        asm_expression(right, scope, gen)
        + "push rax\n"
        + asm_expression(left, scope, gen)
        + "pop rbx\n"
    )
    if op in _ARITH:
        return base + f"{_ARITH[op]} rax, rbx\n"
    if op == "/":
        return base + "cqo\nidiv rbx\n"          # division entière signée
    if op in _CMP:
        return base + f"cmp rax, rbx\n{_CMP[op]} al\nmovzx rax, al\n"
    raise NotImplementedError(f"opérateur inconnu : {op!r}")


def _asm_acces_index(ast: Tree, scope: object, gen: Gen) -> str:
    name: str = _ident(ast.children[0])
    vtype: str = gen.symtab.type_of(name)
    if vtype == "array":
        return codegen_array.asm_get(ast, scope, gen)
    if vtype == "dict":
        return codegen_dict.asm_get(ast, scope, gen)
    raise TypeError(f"indexation impossible : {name!r} est de type {vtype!r}")


def _asm_longueur(ast: Tree, scope: object, gen: Gen) -> str:
    arg: Tree = _tree(ast.children[0])
    if arg.data != "variable":
        raise NotImplementedError("len(...) attend une variable tableau/dict")
    name: str = _ident(arg.children[0])
    vtype: str = gen.symtab.type_of(name)
    if vtype == "array":
        return codegen_array.asm_len(name, gen)
    if vtype == "dict":
        return codegen_dict.asm_len(name, gen)
    raise TypeError(f"len(...) impossible : {name!r} est de type {vtype!r}")


# ── commandes ─────────────────────────────────────────────────────────────


def asm_commande(ast: Tree, scope: object, gen: Gen) -> str:
    data: str = ast.data
    if data == "sequence":
        return "".join(asm_commande(_tree(c), scope, gen) for c in ast.children)
    if data == "assignation":
        return _asm_assignation(ast, scope, gen)
    if data == "assignation_index":
        return _asm_assignation_index(ast, scope, gen)
    if data == "pass":
        return "nop\n"
    if data == "print":
        return _asm_print(_tree(ast.children[0]), scope, gen)
    if data == "if":
        return _asm_if(ast, scope, gen)
    if data == "while":
        return _asm_while(ast, scope, gen)
    if data == "decl_tableau":
        return codegen_array.asm_decl(ast, scope, gen)
    if data == "for_in":
        return codegen_dict.asm_for_in(ast, scope, gen)
    if data == "del_index":
        return codegen_dict.asm_del(ast, scope, gen)
    raise NotImplementedError(f"commande non gérée : {data!r}")


def _asm_assignation(ast: Tree, scope: object, gen: Gen) -> str:
    name: str = _ident(ast.children[0])
    rhs: Tree = _tree(ast.children[1])
    if rhs.data == "dict_vide":
        return codegen_dict.asm_new(name, gen)
    if rhs.data == "dict_literal":
        return codegen_dict.asm_literal(name, rhs, scope, gen)
    code: str = asm_expression(rhs, scope, gen)
    code += f"mov {var_operand(name, scope, gen)}, rax\n"
    return code


def _asm_assignation_index(ast: Tree, scope: object, gen: Gen) -> str:
    name: str = _ident(ast.children[0])
    vtype: str = gen.symtab.type_of(name)
    if vtype == "array":
        return codegen_array.asm_set(ast, scope, gen)
    if vtype == "dict":
        return codegen_dict.asm_set(ast, scope, gen)
    raise TypeError(f"affectation indexée impossible sur {name!r} ({vtype!r})")


def _asm_print(expr: Tree, scope: object, gen: Gen) -> str:
    code: str = asm_expression(expr, scope, gen)
    code += "mov rsi, rax\n"
    code += "mov rdi, format\n"
    code += "xor eax, eax\n"
    code += "call printf\n"
    return code


def _asm_if(ast: Tree, scope: object, gen: Gen) -> str:
    test: str = asm_expression(_tree(ast.children[0]), scope, gen)
    body: str = asm_commande(_tree(ast.children[1]), scope, gen)
    lab: str = gen.new_label("if")
    return test + f"cmp rax, 0\njz {lab}_end\n" + body + f"{lab}_end:\n"


def _asm_while(ast: Tree, scope: object, gen: Gen) -> str:
    test: str = asm_expression(_tree(ast.children[0]), scope, gen)
    body: str = asm_commande(_tree(ast.children[1]), scope, gen)
    lab: str = gen.new_label("while")
    return (
        f"{lab}_start:\n"
        + test
        + f"cmp rax, 0\njz {lab}_end\n"
        + body
        + f"jmp {lab}_start\n{lab}_end:\n"
    )


# ── initialisation des paramètres du main depuis argv ─────────────────────


def asm_init_params(symtab: SymbolTable) -> str:
    """Initialise chaque paramètre du main depuis argv[i+1] via atoi.

    Si l'argument est absent (pointeur NULL), la variable reste à 0 (pas de
    crash). argv[0] est le nom du programme, donc le i-ème paramètre lit
    argv[i+1].
    """
    code: str = ""
    for i, name in enumerate(symtab.init_params()):
        lab: str = symtab.new_label("init")
        gv: str = symtab.gv(name)
        code += "mov rdi, [argv]\n"
        code += f"mov rdi, [rdi + {(i + 1) * 8}]\n"
        code += "test rdi, rdi\n"
        code += f"jz {lab}_null\n"
        code += "call atoi\n"
        code += f"mov [{gv}], rax\n"
        code += f"jmp {lab}_done\n"
        code += f"{lab}_null:\n"
        code += f"mov qword [{gv}], 0\n"
        code += f"{lab}_done:\n"
    return code


# ── pré-passe : construction de la table des symboles ─────────────────────


def build_symbols(programme: Tree, symtab: SymbolTable) -> None:
    """Parcourt le programme pour déclarer fonctions et variables globales.

    Précondition : `programme.children == [fonction*, main]` (main en dernier).
    """
    children: list[Tree] = [_tree(c) for c in programme.children]
    funcs: list[Tree] = children[:-1]
    main: Tree = children[-1]
    for f in funcs:
        _register_function(f, symtab)
    _register_main(main, symtab)


def _register_function(f: Tree, symtab: SymbolTable) -> None:
    ch: list[object] = list(f.children)
    name: str = _ident(ch[0])
    params: list[str] = []
    idx: int = 1
    if isinstance(ch[1], Tree) and ch[1].data == "liste_params":
        params = [_ident(t) for t in ch[1].children]
        idx = 2
    body: Tree = _tree(ch[idx])
    ret: Tree = _tree(ch[idx + 1])
    locals_list: list[str] = list(params)
    _collect_func(body, locals_list)
    symtab.declare_function(FuncInfo(name, params, locals_list, body, ret))


def _collect_func(node: Tree, locals_list: list[str]) -> None:
    """Collecte les variables locales d'une fonction (entiers, sur la pile).

    Refuse explicitement les structures composites dans une fonction (v1).
    """
    data: str = node.data
    if data == "sequence":
        for c in node.children:
            _collect_func(_tree(c), locals_list)
    elif data == "assignation":
        rhs: Tree = _tree(node.children[1])
        if rhs.data in ("dict_vide", "dict_literal"):
            raise NotImplementedError("pas de dict dans une fonction (v1)")
        name: str = _ident(node.children[0])
        if name not in locals_list:
            locals_list.append(name)
    elif data in ("if", "while"):
        _collect_func(_tree(node.children[1]), locals_list)
    elif data in ("decl_tableau", "for_in", "del_index", "assignation_index"):
        raise NotImplementedError(
            "tableaux/dicts seulement dans main en v1 (pas dans une fonction)"
        )
    # print / pass : rien à collecter


def _register_main(main: Tree, symtab: SymbolTable) -> None:
    vars_node: Tree = _tree(main.children[0])
    for t in vars_node.children:
        symtab.declare_main_param(_ident(t))
    _collect_main(_tree(main.children[1]), symtab)


def _collect_main(node: Tree, symtab: SymbolTable) -> None:
    """Déclare les variables globales du main avec leur type."""
    data: str = node.data
    if data == "sequence":
        for c in node.children:
            _collect_main(_tree(c), symtab)
    elif data == "assignation":
        name: str = _ident(node.children[0])
        rhs: Tree = _tree(node.children[1])
        if rhs.data in ("dict_vide", "dict_literal"):
            symtab.declare_global(name, "dict")
        else:
            symtab.declare_global(name, "int")
    elif data == "decl_tableau":
        symtab.declare_global(_ident(node.children[0]), "array")
    elif data == "for_in":
        symtab.declare_global(_ident(node.children[0]), "int")  # variable de boucle
        _collect_main(_tree(node.children[2]), symtab)
    elif data in ("if", "while"):
        _collect_main(_tree(node.children[1]), symtab)
    # assignation_index / del_index / print / pass : aucune nouvelle déclaration


# ── helpers de lecture d'AST ──────────────────────────────────────────────


def _ident(node: object) -> str:
    if not isinstance(node, Token):
        raise TypeError(f"identifiant attendu, reçu {type(node).__name__}")
    return node.value


def _token(node: object) -> str:
    if not isinstance(node, Token):
        raise TypeError(f"jeton attendu, reçu {type(node).__name__}")
    return node.value


def _tree(node: object) -> Tree:
    if not isinstance(node, Tree):
        raise TypeError(f"sous-arbre attendu, reçu {type(node).__name__}")
    return node
