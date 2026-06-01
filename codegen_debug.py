"""Pretty-print : reconstruit du nanoC lisible depuis l'AST (mode `--pp`)."""

from __future__ import annotations

from lark import Tree

import codegen_array
import codegen_dict
import codegen_func
from codegen_ast import ident, indent_block, token, tree
from symboltable import SymbolTable

# Type hint léger pour éviter l'import circulaire de codegen_hub.Pp
_Pp = object


def pp_expression(ast: Tree, pp: _Pp) -> str:
    data: str = ast.data
    if data == "variable":
        return ident(ast.children[0])
    if data == "entier":
        return token(ast.children[0])
    if data == "binaire":
        left: str = pp_expression(tree(ast.children[0]), pp)
        op: str = token(ast.children[1])
        right: str = pp_expression(tree(ast.children[2]), pp)
        return f"{left} {op} {right}"
    if data == "appel_fonction":
        return codegen_func.pp_appel(ast, pp)
    if data == "acces_index":
        return _pp_acces_index(ast, pp)
    if data == "longueur":
        return _pp_longueur(ast, pp)
    if data == "dict_vide":
        return "dict()"
    if data == "dict_literal":
        return codegen_dict.pp_literal_expr(ast, pp)
    raise NotImplementedError(f"expression pp non gérée : {data!r}")


def _pp_acces_index(ast: Tree, pp: _Pp) -> str:
    name: str = ident(ast.children[0])
    symtab: SymbolTable | None = pp.symtab  # type: ignore[attr-defined]
    if symtab is not None and symtab.is_global(name):
        vtype: str = symtab.type_of(name)
        if vtype == "array":
            return codegen_array.pp_get(ast, pp)
        if vtype == "dict":
            return codegen_dict.pp_get(ast, pp)
    return codegen_array.pp_get(ast, pp)


def _pp_longueur(ast: Tree, pp: _Pp) -> str:
    arg: Tree = tree(ast.children[0])
    if arg.data == "variable":
        name: str = ident(arg.children[0])
        symtab: SymbolTable | None = pp.symtab  # type: ignore[attr-defined]
        if symtab is not None and symtab.is_global(name):
            vtype: str = symtab.type_of(name)
            if vtype == "array":
                return codegen_array.pp_len(name, pp)
            if vtype == "dict":
                return codegen_dict.pp_len(name, pp)
        return f"len({name})"
    inner: str = pp_expression(arg, pp)
    return f"len({inner})"


def pp_commande(ast: Tree, pp: _Pp) -> str:
    data: str = ast.data
    if data == "sequence":
        lines: list[str] = [pp_commande(tree(c), pp) for c in ast.children]
        return "\n".join(lines)
    if data == "assignation":
        return _pp_assignation(ast, pp)
    if data == "assignation_index":
        return _pp_assignation_index(ast, pp)
    if data == "pass":
        return "pass;"
    if data == "print":
        return f"print({pp_expression(tree(ast.children[0]), pp)});"
    if data == "if":
        test: str = pp_expression(tree(ast.children[0]), pp)
        body: str = indent_block(pp_commande(tree(ast.children[1]), pp))
        return f"if ({test}) {{\n{body}\n}}"
    if data == "while":
        test: str = pp_expression(tree(ast.children[0]), pp)
        body: str = indent_block(pp_commande(tree(ast.children[1]), pp))
        return f"while ({test}) {{\n{body}\n}}"
    if data == "decl_tableau":
        return codegen_array.pp_decl(ast, pp)
    if data == "for_in":
        return codegen_dict.pp_for_in(ast, pp)
    if data == "del_index":
        return codegen_dict.pp_del(ast, pp)
    raise NotImplementedError(f"commande pp non gérée : {data!r}")


def _pp_assignation(ast: Tree, pp: _Pp) -> str:
    name: str = ident(ast.children[0])
    rhs: Tree = tree(ast.children[1])
    if rhs.data == "dict_vide":
        return codegen_dict.pp_new(name, pp)
    if rhs.data == "dict_literal":
        return codegen_dict.pp_assign_literal(name, rhs, pp)
    rhs_s: str = pp_expression(rhs, pp)
    return f"{name} = {rhs_s};"


def _pp_assignation_index(ast: Tree, pp: _Pp) -> str:
    name: str = ident(ast.children[0])
    symtab: SymbolTable | None = pp.symtab  # type: ignore[attr-defined]
    if symtab is not None and symtab.is_global(name):
        vtype: str = symtab.type_of(name)
        if vtype == "array":
            return codegen_array.pp_set(ast, pp)
        if vtype == "dict":
            return codegen_dict.pp_set(ast, pp)
    return codegen_array.pp_set(ast, pp)
