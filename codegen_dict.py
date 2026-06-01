"""Dev B — Dictionnaires int->int (À IMPLÉMENTER).

Ce fichier est un SQUELETTE : signatures fixées, corps assembleur à écrire.
Ne change pas les signatures : `codegen_base.py` appelle ces fonctions.

────────────────────────────────────────────────────────────────────────────
MODÈLE MÉMOIRE (sans runtime C, fourni par symboltable.py / emit_data)
  Un dict `d` est représenté par des tableaux parallèles statiques (capacité
  fixe CAP) + deux compteurs :
    - st.dk(name)     -> `dk_d`     : clés         (times CAP dq 0)
    - st.dv(name)     -> `dv_d`     : valeurs      (times CAP dq 0)
    - st.du(name)     -> `du_d`     : 1=occupé/0=libre (times CAP dq 0)
    - st.dcount(name) -> `dcount_d` : indice du prochain ajout (dq 0)
    - st.dsize(name)  -> `dsize_d`  : nombre d'entrées vivantes (dq 0) = len

ALGORITHME CONSEILLÉ : balayage linéaire (pas de hachage en v1).
  - set : chercher la clé sur [0, dcount) parmi les slots occupés ; trouvée ->
          mettre à jour dv ; sinon -> écrire au slot `dcount`, puis dcount++ et
          dsize++.
  - get : chercher la clé ; trouvée -> dv ; sinon -> 0 (pas d'erreur en v1).
  - del : chercher la clé ; trouvée -> du=0 et dsize-- ; sinon -> rien.
  - for (k in d) : balayer [0, dcount), traiter les slots où du==1.

OUTILS FOURNIS via `gen` :
  - gen.expr(ast, scope) -> str  : génère une expression ; RÉSULTAT DANS rax.
  - gen.cmd(ast, scope)  -> str  : génère une commande (corps de boucle).
  - gen.symtab           : labels ci-dessus + CAP (gen.symtab.CAP).
  - gen.new_label(pfx)   -> str  : étiquette unique (indispensable pour boucles).

CONSEILS PILE / ALIGNEMENT (ABI System V) :
  - Avant un `call` (ex. dans un corps de for_in qui appelle une fonction),
    rsp doit être aligné sur 16. Si tu sauvegardes un compteur avec `push`,
    pense à compenser (ex. `sub rsp, 8`) pour rester aligné.

INTERDICTION : ne PAS importer codegen_array / codegen_func / codegen_base.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from lark import Token, Tree


def asm_new(name: str, gen: object) -> str:
    """`d = dict();` : vide le dictionnaire.

    À faire : dcount_d = 0, dsize_d = 0, et mettre tous les du_d[i]=0 pour
    i dans [0, CAP) (boucle avec une étiquette via gen.new_label).
    """
    raise NotImplementedError("Dev B : à implémenter — dict() (vidage)")


def asm_literal(name: str, rhs: Tree, scope: object, gen: object) -> str:
    """`d = {k1:v1, ...};` : vide puis insère chaque paire.

    AST : rhs.data == "dict_literal" ; rhs.children[0].data == "paires" ;
    chaque `paire` a children = [expression_clé, expression_valeur].
    Astuce : réutilise la logique de vidage (asm_new) puis d'insertion (asm_set).
    """
    raise NotImplementedError("Dev B : à implémenter — littéral {k:v, ...}")


def asm_set(ast: Tree, scope: object, gen: object) -> str:
    """`d[k] = v;` : insère ou met à jour (balayage linéaire).

    AST : ast.children = [Token(nom), expression_clé, expression_valeur].
    """
    raise NotImplementedError("Dev B : à implémenter — d[k] = v")


def asm_get(ast: Tree, scope: object, gen: object) -> str:
    """`d[k]` : met la valeur associée dans rax (0 si clé absente).

    AST : ast.children = [Token(nom), expression_clé].
    """
    raise NotImplementedError("Dev B : à implémenter — lecture d[k]")


def asm_len(name: str, gen: object) -> str:
    """`len(d)` : nombre d'entrées vivantes (rax <- dsize_d)."""
    raise NotImplementedError("Dev B : à implémenter — len(d)")


def asm_del(ast: Tree, scope: object, gen: object) -> str:
    """`del d[k];` : libère le slot de la clé et décrémente dsize (rien si absent).

    AST : ast.children = [Token(nom), expression_clé].
    """
    raise NotImplementedError("Dev B : à implémenter — del d[k]")


def pp_new(name: str, pp: object) -> str:
    """`d = dict();`"""
    return f"{name} = dict();"


def pp_assign_literal(name: str, rhs: Tree, pp: object) -> str:
    """`d = {k:v, ...};` (commande)."""
    return f"{name} = {pp_literal_expr(rhs, pp)};"


def pp_literal_expr(rhs: Tree, pp: object) -> str:
    """`{k1:v1, k2:v2}` (expression)."""
    paires: Tree = _tree(rhs.children[0])
    parts: list[str] = []
    for paire in paires.children:
        paire_t: Tree = _tree(paire)
        key: str = pp.expr(_tree(paire_t.children[0]))  # type: ignore[attr-defined]
        val: str = pp.expr(_tree(paire_t.children[1]))  # type: ignore[attr-defined]
        parts.append(f"{key}:{val}")
    return "{" + ", ".join(parts) + "}"


def pp_set(ast: Tree, pp: object) -> str:
    """`d[k] = v;`"""
    name: str = _ident(ast.children[0])
    key: str = pp.expr(_tree(ast.children[1]))  # type: ignore[attr-defined]
    val: str = pp.expr(_tree(ast.children[2]))  # type: ignore[attr-defined]
    return f"{name}[{key}] = {val};"


def pp_get(ast: Tree, pp: object) -> str:
    """`d[k]` (expression)."""
    name: str = _ident(ast.children[0])
    key: str = pp.expr(_tree(ast.children[1]))  # type: ignore[attr-defined]
    return f"{name}[{key}]"


def pp_len(name: str, pp: object) -> str:
    """`len(d)`"""
    return f"len({name})"


def pp_del(ast: Tree, pp: object) -> str:
    """`del d[k];`"""
    name: str = _ident(ast.children[0])
    key: str = pp.expr(_tree(ast.children[1]))  # type: ignore[attr-defined]
    return f"del {name}[{key}];"


def pp_for_in(ast: Tree, pp: object) -> str:
    """`for (k in d) { ... }`"""
    k_name: str = _ident(ast.children[0])
    d_name: str = _ident(ast.children[1])
    body: str = pp.cmd(_tree(ast.children[2]))  # type: ignore[attr-defined]
    from codegen_base import _indent_block

    return f"for ({k_name} in {d_name}) {{\n{_indent_block(body)}\n}}"


def asm_for_in(ast: Tree, scope: object, gen: object) -> str:
    """`for (k in d) { ... }` : itère sur les clés des slots occupés.

    AST : ast.children = [Token(var_boucle), Token(nom_dict), bloc].
    À faire : balayer [0, dcount), pour chaque du==1 mettre la clé dans la
    variable de boucle (globale : st.gv(var)), puis générer le corps avec
    gen.cmd(bloc, scope). Protège ton compteur autour du corps (push/pop) et
    garde l'alignement de pile (voir CONSEILS PILE ci-dessus).
    Précondition v1 : scope is None (variable de boucle = globale du main).
    """
    raise NotImplementedError("Dev B : à implémenter — for (k in d)")


# ── helpers de lecture d'AST (réutilisables) ──────────────────────────────


def _ident(node: object) -> str:
    if not isinstance(node, Token):
        raise TypeError(f"identifiant attendu, reçu {type(node).__name__}")
    return node.value


def _tree(node: object) -> Tree:
    if not isinstance(node, Tree):
        raise TypeError(f"sous-arbre attendu, reçu {type(node).__name__}")
    return node
