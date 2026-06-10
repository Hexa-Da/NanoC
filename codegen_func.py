"""Dev A — Fonctions, ABI System V AMD64 / Linux

────────────────────────────────────────────────────────────────────────────
RAPPELS ABI System V (Linux x86_64)
  - Arguments passés dans : rdi, rsi, rdx, rcx, r8, r9 (voir symboltable.ARG_REGS).
  - Valeur de retour dans rax.
  - rsp doit être aligné sur 16 octets juste avant un `call`.

MODÈLE PILE (fourni par symboltable.FuncInfo)
  - Les paramètres et variables locales sont des ENTIERS sur la pile.
  - La i-ème variable locale est à `[rbp - info.offset(nom)]`.
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

from lark import Tree
from codegen_ast import ident, tree
from codegen_analyse import ErreurCompilation, checktype
from symboltable import ARG_REGS, MAX_ARGS, FuncInfo


###### FONCTIONS ASM ######

def asm_fonction(info: FuncInfo, gen: object) -> str:
    """ Génère le corps assembleur d'une fonction. """
    

    func_nom = gen.symtab.func_label(info.name)
    asm_code = f"{func_nom}:\n"

    if len(info.params) > MAX_ARGS:
        raise ErreurCompilation(f"Trop d'arguments pour : {info.name}.")

    ### PROLOGUE ### 
    # On sauvegarde la base + actualisation sommet
    asm_code += "push rbp\n"
    asm_code += "mov rbp, rsp\n"

    # Préparation de la pile
    taille = info.frame_size()
    if taille > 0:
        asm_code += f"sub rsp, {taille}\n"

    # Copie des arguments depuis les registres vers pile locale
    for idx in range(len(info.params)):
        offset = info.offset(info.params[idx])
        registre = ARG_REGS[idx]
        asm_code += f"mov [rbp - {offset}], {registre}\n"
        
    ### CORPS ###
    # Il s'agit de commandes -> on utilise directement le fichier commun
    asm_code += gen.cmd(info.body, info)
    
    ### RETOUR ###
    # Il s'agit d'une expression -> fichier commun
    asm_code += gen.expr(info.ret, info)

    ### EPILOGUE ###
    asm_code += "mov rsp, rbp\n"
    asm_code += "pop rbp\n"
    asm_code += "ret\n"
    
    return asm_code




def asm_appel(ast: Tree, scope: object, gen: object) -> str:
    """ 
    Evalue un appel de fonction. 
    On effectue aussi des vérifications de nombre d'arguments.
    """

    nom = ident(ast.children[0])
    
    # Sécurité d'existence de la fonction appelée
    try:
        info = gen.symtab.lookup_function(nom)
    except NameError:
        raise ErreurCompilation(f"La fonction : {nom} n'est pas définie.")

    # On construit liste arguments + test validité
    if len(ast.children) == 1:
        args = []
    else:
        args = tree(ast.children[1]).children
    
    if len(args) != len(info.params):
        raise ErreurCompilation(f"Mauvais nombre d'arguments pour : {nom}.")
    if len(args) > MAX_ARGS:
        raise ErreurCompilation(f"Trop d'arguments pour : {nom}.")

    # Vérification de type sur chaque argument
    # Chaque expression passée en arg doit être un entier.
    for idx, arg in enumerate(args):
        checktype(tree(arg), scope, gen.symtab, "int", f"argument {idx + 1} de l'appel à '{nom}'")

    asm_code = ""

    # Alignement : juste avant un call, rsp doit être multiple de 16.
    # rsp est déjà décalé de 8 (push rbp du prologue) : un nombre pair de push supplémentaires laisse ce décalage intact.    
    # Donc on doit compenser avec un sub rsp, 8.
    n = len(args)
    if (n % 2 == 0):
        asm_code += "sub rsp, 8\n"

    # On évalue chaque argument (dans rax) puis on le stocke sur la pile

    for idx in range(n): 
        asm_code += gen.expr(args[idx], scope)
        asm_code += "push rax\n"

    # On dépile les arguments dans les registres (ordre inverse)
    # De cette façon on écrase pas d'éventuels calculs d'args
    for idx in range(n-1, -1, -1):
        registre = ARG_REGS[idx]
        asm_code += f"pop {registre}\n"
    
    # Appel de la fonction
    func_nom = gen.symtab.func_label(nom)
    asm_code += f"call {func_nom}\n"

    # On retire le décalage d'alignement si on en avait ajouté un
    if (n%2 == 0):
        asm_code += "add rsp, 8\n"
    
    return asm_code



###### FONCTIONS PP ######

def pp_fonction(ast: Tree, pp: object) -> str:
    """ Pretty-print une fonction. """
    
    # On évite l'import circulaire ici 
    from codegen_ast import pp_liste_params, indent_block

    nom = ident(ast.children[0])
    idx = 1

    ### PARAMETRES ###
    # Disjonction de cas (0 ou > 0 params)
    parametres = ""

    if len(ast.children) > 1 and isinstance(ast.children[1], Tree):
        if ast.children[1].data == "liste_params":
            parametres = pp_liste_params(ast.children[1])
            idx = 2
    
    ### CORPS ###
    corps_ast = tree(ast.children[idx])
    
    # On ajoute direct l'indentation
    corps = indent_block(pp.cmd(corps_ast)) 

    ### RETOUR ###
    ret = pp.expr(tree(ast.children[idx + 1]))  

    ### CHAINE COMPLETE ###
    return f"function {nom}({parametres}) {{\n{corps}\n    return {ret};\n}}"


def pp_appel(ast: Tree, pp: object) -> str:
    """ Pretty-print un appel de fonction. """
    
    nom = ident(ast.children[0])
    
    ### ARGUMENTS ###
    # Disjonction de cas (0 ou >0 args)
    if len(ast.children) == 1:
        return f"{nom}()"
    
    arguments_ast = tree(ast.children[1])
    arguments = ", ".join(pp.expr(tree(c)) for c in arguments_ast.children) 
    
    ### CHAINE COMPLETE ###
    return f"{nom}({arguments})"




