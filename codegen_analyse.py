"""Analyse du programme : remplit la table des symboles avant la génération."""

from __future__ import annotations

from lark import Tree

from codegen_ast import ident, tree
from symboltable import FuncInfo, SymbolTable


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
