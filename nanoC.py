"""NanoC — interpréteur d'un mini-langage type C/Python.

Pipeline :
    source.c  →  Lark (grammaire ci-dessous)  →  AST  →  interp.run

Usage :
    python nanoC.py [arg1 arg2 ...]

Le programme est toujours lu depuis `source.c` à la racine du dépôt.
Les arguments numériques sont passés au `main(...)` du programme.
"""

import sys
from pathlib import Path
from typing import Final

import lark
from lark import Tree

from interp import run

GRAMMAIRE: Final[str] = r"""
IDENTIFIER: /(?!(?:function|return|main|if|while|for|in|del|print|len|dict|int|pass)\b)[a-zA-Z_][a-zA-Z_0-9]*/
OPBIN: /==|!=|[+\-*\/<>]/

programme : fonction* main

fonction : "function" IDENTIFIER "(" params? ")" "{" bloc "return" expression ";" "}"
params : IDENTIFIER ("," IDENTIFIER)* -> liste_params

main : "main" "(" vars ")" "{" bloc "return" expression ";" "}"
vars : IDENTIFIER ("," IDENTIFIER)* -> liste_vars

bloc : commande* -> sequence

expression : IDENTIFIER -> variable
           | SIGNED_NUMBER -> entier
           | expression OPBIN expression -> binaire
           | IDENTIFIER "(" args? ")" -> appel_fonction
           | IDENTIFIER "[" expression "]" -> acces_index
           | "len" "(" expression ")" -> longueur
           | "dict" "(" ")" -> dict_vide
           | "{" paires "}" -> dict_literal

args : expression ("," expression)*
paires : paire ("," paire)*
paire : expression ":" expression

commande : IDENTIFIER "=" expression ";" -> assignation
         | IDENTIFIER "[" expression "]" "=" expression ";" -> assignation_index
         | "pass" -> pass
         | "print" "(" expression ")" ";" -> print
         | "if" "(" expression ")" "{" bloc "}" -> if
         | "while" "(" expression ")" "{" bloc "}" -> while
         | "int" IDENTIFIER "[" expression "]" ";" -> decl_tableau
         | "for" "(" IDENTIFIER "in" IDENTIFIER ")" "{" bloc "}" -> for_in
         | "del" IDENTIFIER "[" expression "]" ";" -> del_index

%import common.WS
%import common.SIGNED_NUMBER
%ignore WS
"""

parseur: Final[lark.Lark] = lark.Lark(GRAMMAIRE, start="programme")
SOURCE_C: Final[Path] = Path(__file__).resolve().parent / "source.c"

def parse_argv(raw: list[str]) -> list[int]:
    """Convertit les arguments CLI en entiers pour le main du programme."""
    args: list[int] = []
    for token in raw:
        try:
            args.append(int(token))
        except ValueError:
            sys.exit(f"argument non entier : {token!r}")
    return args

def main() -> None:
    argv_int: list[int] = parse_argv(sys.argv[1:])
    with open(SOURCE_C, encoding="utf-8") as f:
        src: str = f.read()
    tree: Tree = parseur.parse(src)
    code_retour: int = run(tree, argv_int)
    sys.exit(code_retour)

if __name__ == "__main__":
    main()
