"""Utilitaires partagés pour lire l'AST Lark (aucune génération de code)."""

from __future__ import annotations

from lark import Token, Tree


def ident(node: object) -> str:
    if not isinstance(node, Token):
        raise TypeError(f"identifiant attendu, reçu {type(node).__name__}")
    return node.value


def token(node: object) -> str:
    if not isinstance(node, Token):
        raise TypeError(f"jeton attendu, reçu {type(node).__name__}")
    return node.value


def tree(node: object) -> Tree:
    if not isinstance(node, Tree):
        raise TypeError(f"sous-arbre attendu, reçu {type(node).__name__}")
    return node


def indent_block(text: str, spaces: int = 4) -> str:
    if not text.strip():
        return ""
    prefix: str = " " * spaces
    return "\n".join(prefix + line for line in text.splitlines())


def pp_liste_vars(ast: Tree) -> str:
    """`x, y, z` à partir du nœud `liste_vars`."""
    return ", ".join(ident(t) for t in ast.children)


def pp_liste_params(ast: Tree) -> str:
    """Paramètres d'une fonction."""
    return ", ".join(ident(t) for t in ast.children)
