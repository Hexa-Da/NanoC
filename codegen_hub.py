"""Hub : contextes Gen/Pp et dispatch vers lang + features (array, dict, func)."""

from __future__ import annotations

from lark import Tree

import codegen_array
import codegen_dict
import codegen_func
import codegen_lang
from codegen_analyse import checktype
from codegen_ast import ident, tree
from symboltable import SymbolTable


class Gen:
    """Contexte de génération assembleur passé aux modules de feature."""

    def __init__(self, symtab: SymbolTable) -> None:
        self.symtab: SymbolTable = symtab

    def expr(self, ast: Tree, scope: object) -> str:
        return asm_expression(ast, scope, self)

    def cmd(self, ast: Tree, scope: object) -> str:
        return asm_commande(ast, scope, self)

    def new_label(self, prefix: str) -> str:
        return self.symtab.new_label(prefix)


class Pp:
    """Contexte de pretty-print passé aux modules de feature."""

    def __init__(self, symtab: SymbolTable | None = None) -> None:
        self.symtab: SymbolTable | None = symtab

    def expr(self, ast: Tree) -> str:
        from codegen_debug import pp_expression

        return pp_expression(ast, self)

    def cmd(self, ast: Tree) -> str:
        from codegen_debug import pp_commande

        return pp_commande(ast, self)


# ── assembleur : dispatch ─────────────────────────────────────────────────


def asm_expression(ast: Tree, scope: object, gen: Gen) -> str:
    data: str = ast.data
    if data == "variable":
        return codegen_lang.asm_variable(ast, scope, gen)
    if data == "entier":
        return codegen_lang.asm_entier(ast)
    if data == "binaire":
        return codegen_lang.asm_binaire(ast, scope, gen)
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


def _asm_acces_index(ast: Tree, scope: object, gen: Gen) -> str:
    name: str = ident(ast.children[0])
    indice: Tree = tree(ast.children[1])
    # Précondition : l'indice doit être un entier (pas un tableau ni un dict).
    checktype(indice, scope, gen.symtab, "int", f"indice de '{name}'")
    vtype: str = gen.symtab.type_of(name)
    if vtype == "array":
        return codegen_array.asm_get(ast, scope, gen)
    if vtype == "dict":
        return codegen_dict.asm_get(ast, scope, gen)
    raise TypeError(f"indexation impossible : {name!r} est de type {vtype!r}")


def _asm_longueur(ast: Tree, scope: object, gen: Gen) -> str:
    from codegen_analyse import ErreurCompilation

    arg: Tree = tree(ast.children[0])
    if arg.data != "variable":
        raise NotImplementedError("len(...) attend une variable tableau/dict")
    name: str = ident(arg.children[0])
    vtype: str = gen.symtab.type_of(name)
    # Précondition : len() n'est valide que sur un tableau ou un dictionnaire.
    if vtype == "int":
        raise ErreurCompilation(
            f"len('{name}') interdit : '{name}' est un entier, pas un tableau/dict"
        )
    if vtype == "array":
        return codegen_array.asm_len(name, gen)
    if vtype == "dict":
        return codegen_dict.asm_len(name, gen)
    raise TypeError(f"len(...) impossible : {name!r} est de type {vtype!r}")


def asm_commande(ast: Tree, scope: object, gen: Gen) -> str:
    data: str = ast.data
    if data == "sequence":
        return "".join(asm_commande(tree(c), scope, gen) for c in ast.children)
    if data == "assignation":
        return _asm_assignation(ast, scope, gen)
    if data == "assignation_index":
        return _asm_assignation_index(ast, scope, gen)
    if data == "pass":
        return "nop\n"
    if data == "print":
        return codegen_lang.asm_print(tree(ast.children[0]), scope, gen)
    if data == "if":
        return codegen_lang.asm_if(ast, scope, gen)
    if data == "while":
        return codegen_lang.asm_while(ast, scope, gen)
    if data == "decl_tableau":
        return codegen_array.asm_decl(ast, scope, gen)
    if data == "for_in":
        return codegen_dict.asm_for_in(ast, scope, gen)
    if data == "del_index":
        return codegen_dict.asm_del(ast, scope, gen)
    raise NotImplementedError(f"commande non gérée : {data!r}")


def _asm_assignation(ast: Tree, scope: object, gen: Gen) -> str:
    name: str = ident(ast.children[0])
    rhs: Tree = tree(ast.children[1])
    if rhs.data == "dict_vide":
        return codegen_dict.asm_new(name, gen)
    if rhs.data == "dict_literal":
        return codegen_dict.asm_literal(name, rhs, scope, gen)
    # Précondition : la valeur assignée doit être un entier scalaire.
    checktype(rhs, scope, gen.symtab, "int", f"valeur assignée à '{name}'")
    return codegen_lang.asm_assign_int(name, rhs, scope, gen)


def _asm_assignation_index(ast: Tree, scope: object, gen: Gen) -> str:
    name: str = ident(ast.children[0])
    indice: Tree = tree(ast.children[1])
    valeur: Tree = tree(ast.children[2])
    # Préconditions : indice et valeur doivent être des entiers.
    checktype(indice, scope, gen.symtab, "int", f"indice de '{name}'")
    checktype(valeur, scope, gen.symtab, "int", f"valeur assignée à '{name}[...]'")
    vtype: str = gen.symtab.type_of(name)
    if vtype == "array":
        return codegen_array.asm_set(ast, scope, gen)
    if vtype == "dict":
        return codegen_dict.asm_set(ast, scope, gen)
    raise TypeError(f"affectation indexée impossible sur {name!r} ({vtype!r})")
