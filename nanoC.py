"""Compilateur nanoC : source.c -> resultat.asm (x86-64, Linux, NASM).

Pipeline :
  1. Lark analyse `source.c` selon `grammaire` (axiome = `programme`).
  2. `build_symbols` remplit la table des symboles (types + fonctions).
  3. On génère l'assembleur : définitions de fonctions, déclarations mémoire,
     initialisation des paramètres, corps du main, valeur de retour.
  4. On remplit `squelette.asm` et on écrit `resultat.asm`.

La grammaire reste compatible avec un `main` seul (zéro fonction).
"""

from __future__ import annotations

import lark
from lark import Tree

import codegen_func
from codegen_analyse import ErreurCompilation
from codegen_base import (
    Gen,
    Pp,
    asm_init_params,
    build_symbols,
    pp_commande,
    pp_expression,
    pp_liste_vars,
)
from symboltable import SymbolTable

grammaire: lark.Lark = lark.Lark(
    r"""
IDENTIFIER: /(?!(?:function|main|return|print|if|while|pass|int|for|in|del|len|dict)\b)[a-zA-Z_][a-zA-Z_0-9]*/
OPBIN: /==|!=|[+\-*\/<>]/

programme : fonction* main

fonction : "function" IDENTIFIER "(" liste_params? ")" "{" bloc "return" expression ";" "}"
liste_params : IDENTIFIER ("," IDENTIFIER)*

main : "main" "(" liste_vars ")" "{" bloc "return" expression ";" "}"
liste_vars : (IDENTIFIER ("," IDENTIFIER)*)?

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
         | "pass" ";" -> pass
         | "print" "(" expression ")" ";" -> print
         | "if" "(" expression ")" "{" bloc "}" -> if
         | "while" "(" expression ")" "{" bloc "}" -> while
         | "int" IDENTIFIER "[" expression "]" ";" -> decl_tableau
         | "for" "(" IDENTIFIER "in" IDENTIFIER ")" "{" bloc "}" -> for_in
         | "del" IDENTIFIER "[" expression "]" ";" -> del_index

%import common.WS
%import common.SIGNED_NUMBER
%ignore WS
""",
    start="programme",
)


def asm_programme(ast: Tree) -> str:
    """Génère le code assembleur complet du programme nanoC."""
    symtab: SymbolTable = SymbolTable()
    build_symbols(ast, symtab)
    gen: Gen = Gen(symtab)

    children: list[Tree] = list(ast.children)
    funcs: list[Tree] = children[:-1]
    main: Tree = children[-1]

    func_defs: str = "".join(
        codegen_func.asm_fonction(
            symtab.lookup_function(f.children[0].value), gen
        )
        for f in funcs
    )
    decls: str = symtab.emit_data()
    init: str = asm_init_params(symtab)
    body: str = gen.cmd(main.children[1], None)
    ret: str = gen.expr(main.children[2], None)

    squelette: str = open("squelette.asm").read()
    squelette = squelette.replace("DECL_VARS", decls)
    squelette = squelette.replace("INIT_VARS", init)
    squelette = squelette.replace("FUNCTION_DEFS", func_defs)
    squelette = squelette.replace("COMMAND", body)
    squelette = squelette.replace("RETURN", ret)
    return squelette


def pp_programme(ast: Tree) -> str:
    """Reconstruit le programme nanoC sous forme lisible (debug / cours)."""
    symtab: SymbolTable = SymbolTable()
    build_symbols(ast, symtab)
    pp: Pp = Pp(symtab)

    children: list[Tree] = list(ast.children)
    funcs: list[Tree] = children[:-1]
    main: Tree = children[-1]

    parts: list[str] = [codegen_func.pp_fonction(f, pp) for f in funcs]
    vs: str = pp_liste_vars(main.children[0])
    body: str = pp_commande(main.children[1], pp)
    ret: str = pp_expression(main.children[2], pp)
    from codegen_ast import indent_block

    main_s: str = (
        f"main({vs}) {{\n"
        f"{indent_block(body)}\n"
        f"    return {ret};\n"
        f"}}"
    )
    parts.append(main_s)
    return "\n\n".join(parts)


if __name__ == "__main__":
    import sys

    src: str = open("source.c").read()
    try:
        tree: Tree = grammaire.parse(src)
        if "--pp" in sys.argv or "--pretty" in sys.argv:
            print(pp_programme(tree))
        else:
            with open("resultat.asm", "w") as f:
                f.write(asm_programme(tree))
            print("resultat.asm généré.")
    except lark.exceptions.UnexpectedInput as e:
        print(f"Erreur de syntaxe (ligne {e.line}, col {e.column}) :")
        print(f"  {e.get_context(src, 40)}")
        sys.exit(1)
    except ErreurCompilation as e:
        print(f"Erreur de compilation : {e}")
        sys.exit(1)
