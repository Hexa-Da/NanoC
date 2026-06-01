"""Dev A — Fonctions, ABI System V AMD64 / Linux (À IMPLÉMENTER).

Ce fichier est un SQUELETTE : signatures fixées, corps assembleur à écrire.
Ne change pas les signatures : `codegen_base.py` (appels) et `nanoC.py`
(définitions) appellent ces fonctions.

────────────────────────────────────────────────────────────────────────────
RAPPELS ABI System V (Linux x86_64)
  - Arguments passés dans : rdi, rsi, rdx, rcx, r8, r9 (voir symboltable.ARG_REGS).
  - Valeur de retour dans rax.
  - rsp doit être aligné sur 16 octets juste avant un `call`.

MODÈLE PILE (fourni par symboltable.FuncInfo)
  - Les paramètres et variables locales sont des ENTIERS sur la pile.
  - La i-ème variable locale est à `[rbp - info.offset(nom)]`
    (offset = 8*(index+1)).
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


def asm_appel(ast: Tree, scope: object, gen: object) -> str:
    """`f(a1, ..., an)` : évalue les arguments, appelle, résultat dans rax.

    AST : ast.children = [Token(nom)] (+ noeud `args` si arguments présents,
    args.children = liste d'expressions).
    Plan conseillé :
      - récupérer FuncInfo via gen.symtab.lookup_function(nom) ;
      - VÉRIFIER l'arité (len(args) == len(info.params)) -> sinon TypeError ;
      - refuser > MAX_ARGS arguments (NotImplementedError) ;
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
