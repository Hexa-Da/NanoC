"""Dev B — Dictionnaires int->int

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
    """`d = dict();` : vide le dictionnaire."""
    st: SymbolTable = gen.symtab  # type: ignore[attr-defined]
    du: str = st.du(name)
    dcount: str = st.dcount(name)
    dsize: str = st.dsize(name)
    cap: int = st.CAP
    lab: str = gen.new_label("dict_new")

    return (
        f"mov qword [{dcount}], 0\n"
        f"mov qword [{dsize}], 0\n"
        f"xor rax, rax\n"
        f"{lab}_loop:\n"
        f"cmp rax, {cap}\n"
        f"jge {lab}_end\n"
        f"mov qword [{du} + rax*8], 0\n"
        f"inc rax\n"
        f"jmp {lab}_loop\n"
        f"{lab}_end:\n"
    )


def asm_literal(name: str, rhs: Tree, scope: object, gen: object) -> str:
    """`d = {k1:v1, ...};` : vide puis insère chaque paire."""
    paires: Tree = _tree(rhs.children[0])
    code: str = asm_new(name, gen)

    for paire in paires.children:
        paire_t: Tree = _tree(paire)
        key_expr: Tree = _tree(paire_t.children[0])
        val_expr: Tree = _tree(paire_t.children[1])

        set_ast: Tree = Tree("assignation_index", [Token("IDENTIFIER", name), key_expr, val_expr])
        code += asm_set(set_ast, scope, gen)

    return code


def asm_set(ast: Tree, scope: object, gen: object) -> str:
    """`d[k] = v;` : insère ou met à jour (balayage linéaire)."""
    name: str = _ident(ast.children[0])
    key_ast: Tree = _tree(ast.children[1])
    val_ast: Tree = _tree(ast.children[2])
    
    st: object = gen.symtab 
    dk: str = st.dk(name)
    dv: str = st.dv(name)
    du: str = st.du(name)
    dcount: str = st.dcount(name)
    dsize: str = st.dsize(name)
    cap: int = st.CAP

    lab: str = gen.new_label("dict_set")

    # Préconditions :
    # - key_ast et val_ast évaluent un entier en rax via gen.expr(...)
    # - dcount est dans [0, CAP]
    #
    # Invariant de boucle :
    # - pour tout j dans [0, rdx), aucune entrée occupée ne porte la clé cible
    # - rcx = dcount reste constant pendant le scan

    code: str = ""
    code += gen.expr(val_ast, scope)   # rax = value
    code += "push rax\n"               # push value
    code += gen.expr(key_ast, scope)   # rax = key
    code += "pop rbx\n"                # rbx = value, rax = key
    code += f"mov rcx, [{dcount}]\n"   # rcx = dcount
    code += "xor rdx, rdx\n"           # rdx = i = 0

    # Boucle de scan :
    code += f"{lab}_scan:\n"
    code += "cmp rdx, rcx\n"
    code += f"jge {lab}_not_found\n"

    code += f"cmp qword [{du} + rdx*8], 0\n"
    code += f"je {lab}_next\n"

    code += f"cmp qword [{dk} + rdx*8], rax\n"
    code += f"jne {lab}_next\n"

    # clé trouvée -> update valeur
    code += f"mov qword [{dv} + rdx*8], rbx\n"
    code += f"jmp {lab}_end\n"

    code += f"{lab}_next:\n"
    code += "inc rdx\n"
    code += f"jmp {lab}_scan\n"

    # clé absente -> insertion au slot dcount
    code += f"{lab}_not_found:\n"
    code += f"cmp rcx, {cap}\n"
    code += f"jge {lab}_end\n"  # dict plein : on ignore en v1

    code += f"mov qword [{dk} + rcx*8], rax\n"
    code += f"mov qword [{dv} + rcx*8], rbx\n"
    code += f"mov qword [{du} + rcx*8], 1\n"
    code += "inc rcx\n"
    code += f"mov qword [{dcount}], rcx\n"
    code += f"add qword [{dsize}], 1\n"

    code += f"{lab}_end:\n"
    return code


def asm_get(ast: Tree, scope: object, gen: object) -> str:
    """`d[k]` : met la valeur associée dans rax (0 si clé absente)"""
    name: str = _ident(ast.children[0])
    key_ast: Tree = _tree(ast.children[1])
    
    st: object = gen.symtab 
    dk: str = st.dk(name)
    dv: str = st.dv(name)
    du: str = st.du(name)
    dcount: str = st.dcount(name)
    
    lab: str = gen.new_label("dict_get")

    # Préconditions :
    # - key_ast évalue un entier en rax via gen.expr(...)
    #
    # Invariant de boucle :
    # - pour tout j dans [0, rdx), aucune entrée occupée ne porte la clé cible
    # - rcx = dcount reste constant pendant le scan

    code: str = ""
    code += gen.expr(key_ast, scope)   # rax = key
    code += "mov rbx, rax\n"           # rbx = key
    code += f"mov rcx, [{dcount}]\n"   # rcx = dcount
    code += "xor rdx, rdx\n"           # rdx = i = 0

    # Boucle de scan :
    code += f"{lab}_scan:\n"
    code += "cmp rdx, rcx\n"
    code += f"jge {lab}_not_found\n"

    code += f"cmp qword [{du} + rdx*8], 0\n"
    code += f"je {lab}_next\n"

    code += f"cmp qword [{dk} + rdx*8], rbx\n"
    code += f"jne {lab}_next\n"

    # clé trouvée -> met la valeur dans rax
    code += f"mov rax, qword [{dv} + rdx*8]\n"
    code += f"jmp {lab}_end\n"

    code += f"{lab}_next:\n"
    code += "inc rdx\n"
    code += f"jmp {lab}_scan\n"

    # clé absente -> met 0 dans rax
    code += f"{lab}_not_found:\n"
    code += "xor rax, rax\n"

    code += f"{lab}_end:\n"
    return code


def asm_len(name: str, gen: object) -> str:
    """`len(d)` : nombre d'entiers vivants (rax <- dsize_d)."""
    st: object = gen.symtab
    dsize: str = st.dsize(name)
    return f"mov rax, qword [{dsize}]\n"


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
    from codegen_ast import indent_block

    return f"for ({k_name} in {d_name}) {{\n{indent_block(body)}\n}}"


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
