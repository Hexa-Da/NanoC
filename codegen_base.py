"""Façade du tronc commun — réexporte hub, analyse, lang et debug.

Structure :
  - `codegen_ast`     : lecture de l'AST (_ident, _tree, indentation)
  - `codegen_analyse` : `build_symbols` (pré-passe symtab)
  - `codegen_lang`    : langage de base (entiers, if/while/print, argv)
  - `codegen_hub`     : `Gen`, `Pp`, dispatch vers array / dict / func
  - `codegen_debug`   : pretty-print (`pp_*`, mode `--pp`)

Les imports existants `from codegen_base import ...` restent valides.
"""

from __future__ import annotations

from codegen_analyse import build_symbols
from codegen_ast import ident as _ident
from codegen_ast import indent_block as _indent_block
from codegen_ast import pp_liste_params, pp_liste_vars, token as _token, tree as _tree
from codegen_debug import pp_commande, pp_expression
from codegen_hub import Gen, Pp, asm_commande, asm_expression
from codegen_lang import asm_init_params, var_operand

__all__ = [
    "Gen",
    "Pp",
    "asm_commande",
    "asm_expression",
    "asm_init_params",
    "build_symbols",
    "pp_commande",
    "pp_expression",
    "pp_liste_params",
    "pp_liste_vars",
    "var_operand",
    "_ident",
    "_indent_block",
    "_token",
    "_tree",
]
