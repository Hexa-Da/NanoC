"""Dev C — Tableaux 1D d'entiers (À IMPLÉMENTER).

Ce fichier est un SQUELETTE : les contrats (signatures, ce que chaque fonction
doit renvoyer) sont fixés, à toi d'écrire le corps assembleur. Ne change pas
les signatures : `codegen_base.py` appelle ces fonctions par leur nom.

────────────────────────────────────────────────────────────────────────────
MODÈLE MÉMOIRE (sans runtime C, fourni par symboltable.py / emit_data)
  Un tableau `t` réserve une zone statique de capacité fixe :
    - st.arr_data(name)  -> label `arr_t`    : `times CAP dq 0` (les éléments)
    - st.arr_len(name)   -> label `arrlen_t` : `dq 0`           (longueur réelle)
  Adressage absolu (compatible `gcc -no-pie`) : `[arr_t + rax*8]`.

OUTILS FOURNIS via `gen` (objet de contexte) :
  - gen.expr(ast, scope) -> str : génère une expression ; RÉSULTAT DANS rax.
  - gen.cmd(ast, scope)  -> str : génère une commande.
  - gen.symtab           : la table des symboles (labels ci-dessus, CAP).
  - gen.new_label(pfx)   -> str : étiquette unique (utile pour des boucles).

CONVENTION : chaque `asm_*` renvoie une chaîne assembleur. Les expressions
laissent leur résultat dans rax. `scope` vaut None dans le main (cas des
tableaux en v1), ou une FuncInfo dans une fonction (interdit ici en v1).

INTERDICTION : ne PAS importer codegen_dict / codegen_func / codegen_base.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from lark import Token, Tree


def asm_decl(ast: Tree, scope: object, gen: object) -> str:
    """`int t[E];` : fixe la longueur réelle du tableau.

    AST : ast.children = [Token(nom), expression_E].
    À faire : évaluer E (gen.expr -> rax), puis stocker rax dans `arrlen_t`.
    La zone `arr_t` est déjà mise à zéro par emit_data (rien à initialiser).
    Précondition v1 : scope is None (tableau = globale du main) et 0 <= E <= CAP.
    """
    raise NotImplementedError("Dev C : à implémenter — déclaration de tableau")


def asm_get(ast: Tree, scope: object, gen: object) -> str:
    """`t[i]` : charge l'élément d'indice i dans rax.

    AST : ast.children = [Token(nom), expression_indice].
    Indice : `mov rax, [arr_t + rax*8]` une fois l'indice calculé dans rax.
    """
    raise NotImplementedError("Dev C : à implémenter — lecture t[i]")


def asm_set(ast: Tree, scope: object, gen: object) -> str:
    """`t[i] = v;` : écrit la valeur v à l'indice i.

    AST : ast.children = [Token(nom), expression_indice, expression_valeur].
    Astuce pile : évalue la valeur, empile-la, évalue l'indice, dépile la
    valeur dans rbx, puis `mov [arr_t + rax*8], rbx` (rax = indice).
    """
    raise NotImplementedError("Dev C : à implémenter — écriture t[i] = v")


def asm_len(name: str, gen: object) -> str:
    """`len(t)` : charge la longueur réelle du tableau dans rax (depuis arrlen_t)."""
    raise NotImplementedError("Dev C : à implémenter — len(t)")


# ── pretty-print (texte nanoC lisible, parallèle aux asm_*) ───────────────


def pp_decl(ast: Tree, pp: object) -> str:
    """`int t[E];`"""
    name: str = _ident(ast.children[0])
    size: str = pp.expr(_tree(ast.children[1]))  # type: ignore[attr-defined]
    return f"int {name}[{size}];"


def pp_get(ast: Tree, pp: object) -> str:
    """`t[i]` (expression)."""
    name: str = _ident(ast.children[0])
    idx: str = pp.expr(_tree(ast.children[1]))  # type: ignore[attr-defined]
    return f"{name}[{idx}]"


def pp_set(ast: Tree, pp: object) -> str:
    """`t[i] = v;`"""
    name: str = _ident(ast.children[0])
    idx: str = pp.expr(_tree(ast.children[1]))  # type: ignore[attr-defined]
    val: str = pp.expr(_tree(ast.children[2]))  # type: ignore[attr-defined]
    return f"{name}[{idx}] = {val};"


def pp_len(name: str, pp: object) -> str:
    """`len(t)`"""
    return f"len({name})"


# ── helpers de lecture d'AST (réutilisables) ──────────────────────────────


def _ident(node: object) -> str:
    if not isinstance(node, Token):
        raise TypeError(f"identifiant attendu, reçu {type(node).__name__}")
    return node.value


def _tree(node: object) -> Tree:
    if not isinstance(node, Tree):
        raise TypeError(f"sous-arbre attendu, reçu {type(node).__name__}")
    return node
