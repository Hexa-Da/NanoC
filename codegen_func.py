"""Dev A — Fonctions, ABI System V AMD64 / Linux

────────────────────────────────────────────────────────────────────────────
RAPPELS ABI System V (Linux x86_64)
  - Arguments passés dans : rdi, rsi, rdx, rcx, r8, r9 (voir symboltable.ARG_REGS).
  - Valeur de retour dans rax.
  - rsp doit être aligné sur 16 octets juste avant un `call`.

MODÈLE PILE (fourni par symboltable.FuncInfo)
  - Les paramètres et variables locales sont des ENTIERS sur la pile.
  - La i-ème variable locale est à `[rbp - info.offset(nom)]`.
  - `info.params`      : liste ordonnée des paramètres.
  - `info.locals`      : params + variables locales (les params d'abord).
  - `info.frame_size()`: taille à réserver, déjà alignée sur 16.
  - `gen.symtab.func_label(nom)` -> `func_nom` : étiquette de la fonction.

OUTILS FOURNIS via `gen` :
  - gen.expr(ast, scope) -> str : génère une expression ; RÉSULTAT DANS rax.
  - gen.cmd(ast, scope)  -> str : génère une commande (le corps).
  - gen.symtab           : table des symboles (labels, lookup_function...).

CONVENTION : à l'intérieur d'une fonction, `scope` vaut l'objet FuncInfo
(et non None). Transmets-le tel quel à gen.expr / gen.cmd pour que les
variables soient résolues sur la pile.

INTERDICTION : ne PAS importer codegen_array / codegen_dict / codegen_base.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from lark import Token, Tree

from codegen_analyse import ErreurCompilation
from symboltable import ARG_REGS, MAX_ARGS, FuncInfo


def asm_fonction(info: FuncInfo, gen: object) -> str:
    """Génère le corps assembleur complet d'une fonction utilisateur.

    Plan attendu :
      1. Étiquette `func_nom:` (gen.symtab.func_label(info.name)).
      2. Prologue : `push rbp` ; `mov rbp, rsp` ; `sub rsp, info.frame_size()`.
      3. Copier les paramètres des registres ARG_REGS vers leurs emplacements
         pile : `mov [rbp - info.offset(param)], <reg>`.
      4. Corps : gen.cmd(info.body, info).
      5. Retour : gen.expr(info.ret, info) (résultat dans rax).
      6. Épilogue : `mov rsp, rbp` ; `pop rbp` ; `ret`.
    """
    raise NotImplementedError("Dev A : à implémenter — définition de fonction")


def pp_fonction(ast: Tree, pp: object) -> str:
    """`function f(a, b) { ... return expr; }`"""
    name: str = _ident(ast.children[0])
    params: str = ""
    idx: int = 1
    if len(ast.children) > 1 and isinstance(ast.children[1], Tree):
        if ast.children[1].data == "liste_params":
            from codegen_ast import pp_liste_params

            params = pp_liste_params(ast.children[1])
            idx = 2
    body: Tree = _tree(ast.children[idx])
    ret: str = pp.expr(_tree(ast.children[idx + 1]))  # type: ignore[attr-defined]
    from codegen_ast import indent_block

    body_s: str = indent_block(pp.cmd(body))  # type: ignore[attr-defined]
    return f"function {name}({params}) {{\n{body_s}\n    return {ret};\n}}"


def pp_appel(ast: Tree, pp: object) -> str:
    """`f(a1, a2)` (expression)."""
    name: str = _ident(ast.children[0])
    if len(ast.children) == 1:
        return f"{name}()"
    args_node: Tree = _tree(ast.children[1])
    args: str = ", ".join(pp.expr(_tree(c)) for c in args_node.children)  # type: ignore[attr-defined]
    return f"{name}({args})"


def asm_appel(ast: Tree, scope: object, gen: object) -> str:
    """`f(a1, ..., an)` : évalue les arguments, appelle, résultat dans rax.

    AST : ast.children = [Token(nom)] (+ noeud `args` si arguments présents,
    args.children = liste d'expressions).
    Plan conseillé :
      - récupérer FuncInfo via gen.symtab.lookup_function(nom) ;
      - obtenir le label : gen.symtab.func_label(nom) -> "func_nom" ;
      - VÉRIFIER l'arité (len(args) == len(info.params)) -> sinon
        raise ErreurCompilation(f"...") (pas TypeError : évite le traceback) ;
      - VÉRIFIER > MAX_ARGS arguments -> raise ErreurCompilation(f"...") ;
      - évaluer chaque argument (gen.expr) et l'empiler, puis dépiler dans
        ARG_REGS en ordre inverse (pile équilibrée = alignement préservé) ;
      - `call func_nom`.
    """
    raise NotImplementedError("Dev A : à implémenter — appel de fonction")


# ── helpers de lecture d'AST (réutilisables) ──────────────────────────────


def _ident(node: object) -> str:
    if not isinstance(node, Token):
        raise TypeError(f"identifiant attendu, reçu {type(node).__name__}")
    return node.value


def _tree(node: object) -> Tree:
    if not isinstance(node, Tree):
        raise TypeError(f"sous-arbre attendu, reçu {type(node).__name__}")
    return node
