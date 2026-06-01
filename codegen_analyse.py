"""Analyse du programme : remplit la table des symboles avant la génération.

Exporte aussi `ErreurCompilation`, l'exception unique utilisée dans tout le
compilateur pour signaler une erreur au programmeur nanoC (type incorrect,
variable inconnue, arité mauvaise…). Elle est interceptée dans `nanoC.py`
et affichée sans traceback Python.
"""

from __future__ import annotations

from lark import Tree

from codegen_ast import ident, tree
from symboltable import FuncInfo, SymbolTable


class ErreurCompilation(Exception):
    """Erreur de compilation nanoC — affichée proprement, sans traceback."""


def build_symbols(programme: Tree, symtab: SymbolTable) -> None:
    """Parcourt le programme pour déclarer fonctions et variables globales.

    Précondition : `programme.children == [fonction*, main]` (main en dernier).
    """
    children: list[Tree] = [tree(c) for c in programme.children]
    funcs: list[Tree] = children[:-1]
    main: Tree = children[-1]
    for f in funcs:
        _register_function(f, symtab)
    _register_main(main, symtab)


def _register_function(f: Tree, symtab: SymbolTable) -> None:
    ch: list[object] = list(f.children)
    name: str = ident(ch[0])
    params: list[str] = []
    idx: int = 1
    if isinstance(ch[1], Tree) and ch[1].data == "liste_params":
        params = [ident(t) for t in ch[1].children]
        idx = 2
    body: Tree = tree(ch[idx])
    ret: Tree = tree(ch[idx + 1])
    locals_list: list[str] = list(params)
    _collect_func(body, locals_list)
    symtab.declare_function(FuncInfo(name, params, locals_list, body, ret))


def _collect_func(node: Tree, locals_list: list[str]) -> None:
    """Collecte les variables locales d'une fonction (entiers, sur la pile)."""
    data: str = node.data
    if data == "sequence":
        for c in node.children:
            _collect_func(tree(c), locals_list)
    elif data == "assignation":
        rhs: Tree = tree(node.children[1])
        if rhs.data in ("dict_vide", "dict_literal"):
            raise NotImplementedError("pas de dict dans une fonction (v1)")
        name: str = ident(node.children[0])
        if name not in locals_list:
            locals_list.append(name)
    elif data in ("if", "while"):
        _collect_func(tree(node.children[1]), locals_list)
    elif data in ("decl_tableau", "for_in", "del_index", "assignation_index"):
        raise NotImplementedError(
            "tableaux/dicts seulement dans main en v1 (pas dans une fonction)"
        )


def _register_main(main: Tree, symtab: SymbolTable) -> None:
    vars_node: Tree = tree(main.children[0])
    for t in vars_node.children:
        symtab.declare_main_param(ident(t))
    _collect_main(tree(main.children[1]), symtab)


# ---------------------------------------------------------------------------
# Vérification de types — expr_type / checktype
# ---------------------------------------------------------------------------

def expr_type(ast: Tree, scope: object, symtab: SymbolTable) -> str:
    """Retourne le type de l'expression `ast` : "int", "array" ou "dict".

    Préconditions :
      - `ast` est un nœud d'expression Lark (Tree).
      - `symtab` a déjà été remplie par `build_symbols`.
      - `scope` est soit None (main), soit un objet `FuncInfo` (corps de fonction).

    Invariant : toute expression NanoC a exactement l'un des trois types.
    Lève `ErreurCompilation` si le type ne peut pas être déterminé.
    """
    data: str = ast.data

    if data == "entier":
        return "int"

    if data == "variable":
        name: str = ident(ast.children[0])
        if isinstance(scope, FuncInfo):
            # Les variables locales de fonctions sont toujours des entiers.
            if name not in scope.locals:
                raise ErreurCompilation(
                    f"variable inconnue dans la fonction {scope.name!r} : {name!r}"
                )
            return "int"
        try:
            return symtab.type_of(name)
        except NameError:
            raise ErreurCompilation(f"variable globale inconnue : {name!r}") from None

    if data == "binaire":
        # L'opération elle-même produit un int ; les opérandes seront vérifiés
        # séparément par checktype dans codegen_lang.
        return "int"

    if data == "appel_fonction":
        # Les fonctions nanoC retournent toujours un int.
        return "int"

    if data == "acces_index":
        # t[i] ou d[k] → la valeur stockée est toujours un int.
        return "int"

    if data == "longueur":
        # len(t) → int.
        return "int"

    if data in ("dict_vide", "dict_literal"):
        return "dict"

    raise ErreurCompilation(f"expression de type inconnu : {data!r}")


def checktype(
    ast: Tree,
    scope: object,
    symtab: SymbolTable,
    attendu: str,
    contexte: str = "",
) -> None:
    """Vérifie que le type de `ast` est `attendu`.

    Précondition : `attendu` est "int", "array" ou "dict".
    Lève `ErreurCompilation` avec un message lisible si le type ne correspond pas.
    Le paramètre `contexte` est une courte description de l'endroit où l'erreur
    survient (ex. "opérande gauche de '+'") pour aider le débutant.
    """
    obtenu: str = expr_type(ast, scope, symtab)
    if obtenu != attendu:
        detail: str = f" ({contexte})" if contexte else ""
        raise ErreurCompilation(
            f"type incorrect{detail} : attendu '{attendu}', obtenu '{obtenu}'"
        )


def _collect_main(node: Tree, symtab: SymbolTable) -> None:
    """Déclare les variables globales du main avec leur type."""
    data: str = node.data
    if data == "sequence":
        for c in node.children:
            _collect_main(tree(c), symtab)
    elif data == "assignation":
        name: str = ident(node.children[0])
        rhs: Tree = tree(node.children[1])
        if rhs.data in ("dict_vide", "dict_literal"):
            symtab.declare_global(name, "dict")
        else:
            symtab.declare_global(name, "int")
    elif data == "decl_tableau":
        symtab.declare_global(ident(node.children[0]), "array")
    elif data == "for_in":
        symtab.declare_global(ident(node.children[0]), "int")
        _collect_main(tree(node.children[2]), symtab)
    elif data in ("if", "while"):
        _collect_main(tree(node.children[1]), symtab)
