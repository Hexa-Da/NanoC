"""Langage de base nanoC : entiers, opérateurs, if/while/print, argv du main.

Pas de dispatch vers tableaux / dicts / fonctions (voir `codegen_hub`).
Les fonctions récursives (`_asm_binaire`, etc.) importent `codegen_hub`
à l'intérieur du corps pour éviter les imports circulaires au chargement.
"""

from __future__ import annotations

from lark import Tree

from codegen_ast import ident, token, tree
from symboltable import FuncInfo, SymbolTable

# rax = gauche, rbx = droite après la séquence push/pop standard
_ARITH: dict[str, str] = {"+": "add", "-": "sub", "*": "imul"}
_CMP: dict[str, str] = {"<": "setl", ">": "setg", "==": "sete", "!=": "setne"}


def var_operand(name: str, scope: object, gen: object) -> str:
    """Opérande mémoire d'un entier (`[rbp - d]` ou `[gv_x]`)."""
    st: SymbolTable = gen.symtab  # type: ignore[attr-defined]
    if isinstance(scope, FuncInfo):
        if name in scope.locals:
            return f"[rbp - {scope.offset(name)}]"
        raise NameError(
            f"variable inconnue dans la fonction {scope.name!r} : {name!r}"
        )
    if not st.is_global(name):
        raise NameError(f"variable globale inconnue : {name!r}")
    if st.type_of(name) != "int":
        raise TypeError(f"{name!r} n'est pas un entier scalaire")
    return f"[{st.gv(name)}]"


def asm_variable(ast: Tree, scope: object, gen: object) -> str:
    name: str = ident(ast.children[0])
    return f"mov rax, {var_operand(name, scope, gen)}\n"


def asm_entier(ast: Tree) -> str:
    return f"mov rax, {int(token(ast.children[0]))}\n"


def asm_binaire(ast: Tree, scope: object, gen: object) -> str:
    from codegen_analyse import checktype
    from codegen_hub import asm_expression

    left: Tree = tree(ast.children[0])
    op: str = token(ast.children[1])
    right: Tree = tree(ast.children[2])
    # Précondition : les deux opérandes doivent être des entiers.
    st: SymbolTable = gen.symtab  # type: ignore[attr-defined]
    checktype(left, scope, st, "int", f"opérande gauche de '{op}'")
    checktype(right, scope, st, "int", f"opérande droit de '{op}'")
    base: str = (
        asm_expression(right, scope, gen)
        + "push rax\n"
        + asm_expression(left, scope, gen)
        + "pop rbx\n"
    )
    if op in _ARITH:
        return base + f"{_ARITH[op]} rax, rbx\n"
    if op == "/":
        return base + "cqo\nidiv rbx\n"
    if op in _CMP:
        return base + f"cmp rax, rbx\n{_CMP[op]} al\nmovzx rax, al\n"
    raise NotImplementedError(f"opérateur inconnu : {op!r}")


def asm_print(expr: Tree, scope: object, gen: object) -> str:
    from codegen_analyse import checktype
    from codegen_hub import asm_expression

    # Précondition : print n'accepte que des entiers (printf("%lld", …)).
    st: SymbolTable = gen.symtab  # type: ignore[attr-defined]
    checktype(expr, scope, st, "int", "argument de print")
    code: str = asm_expression(expr, scope, gen)
    code += "mov rsi, rax\n"
    code += "mov rdi, format\n"
    code += "xor eax, eax\n"
    code += "call printf\n"
    return code


def asm_if(ast: Tree, scope: object, gen: object) -> str:
    from codegen_hub import asm_commande, asm_expression

    test: str = asm_expression(tree(ast.children[0]), scope, gen)
    body: str = asm_commande(tree(ast.children[1]), scope, gen)
    lab: str = gen.new_label("if")  # type: ignore[attr-defined]
    return test + f"cmp rax, 0\njz {lab}_end\n" + body + f"{lab}_end:\n"


def asm_while(ast: Tree, scope: object, gen: object) -> str:
    from codegen_hub import asm_commande, asm_expression

    test: str = asm_expression(tree(ast.children[0]), scope, gen)
    body: str = asm_commande(tree(ast.children[1]), scope, gen)
    lab: str = gen.new_label("while")  # type: ignore[attr-defined]
    return (
        f"{lab}_start:\n"
        + test
        + f"cmp rax, 0\njz {lab}_end\n"
        + body
        + f"jmp {lab}_start\n{lab}_end:\n"
    )


def asm_assign_int(name: str, rhs: Tree, scope: object, gen: object) -> str:
    from codegen_hub import asm_expression

    code: str = asm_expression(rhs, scope, gen)
    code += f"mov {var_operand(name, scope, gen)}, rax\n"
    return code


def asm_init_params(symtab: SymbolTable) -> str:
    """Initialise les paramètres du main depuis argv[i+1] (0 si absent)."""
    code: str = ""
    for i, name in enumerate(symtab.init_params()):
        lab: str = symtab.new_label("init")
        gv: str = symtab.gv(name)
        code += "mov rdi, [argv]\n"
        code += f"mov rdi, [rdi + {(i + 1) * 8}]\n"
        code += "test rdi, rdi\n"
        code += f"jz {lab}_null\n"
        code += "call atoi\n"
        code += f"mov [{gv}], rax\n"
        code += f"jmp {lab}_done\n"
        code += f"{lab}_null:\n"
        code += f"mov qword [{gv}], 0\n"
        code += f"{lab}_done:\n"
    return code
