"""Tronc commun — évaluateur récursif de l'AST NanoC.

C'est ici que les trois modules se rejoignent. 
Ce fichier appelle `array_impl`, `dict_impl` et `func_impl`.

Vue d'ensemble :

    run(tree, argv)
        ├── enregistre les fonctions          
        ├── crée la frame globale du main     
        └── Interpreter.execute / evaluate
              ├── arithmétique & contrôle (ici)
              ├── tableaux : NanoArray            
              ├── dictionnaires : NanoDict        
              └── appels : NanoFunction.bind_args 
"""

from __future__ import annotations

from typing import Union

from lark import Token, Tree

from array_impl import NanoArray
from dict_impl import NanoDict
from func_impl import Frame, FunctionTable, NanoFunction

Valeur = Union[int, NanoArray, NanoDict]


def run(tree: Tree, argv: list[int]) -> int:
    """Exécute un programme NanoC complet et retourne le code de sortie.

    Précondition : `tree.data == "programme"`, `argv` ne contient que des
    entiers. La liste `argv` peut être plus courte que les variables du main :
    les variables non initialisées prennent la valeur 0.

    Retour : la valeur entière du `return` du `main`.
    """
    if tree.data != "programme":
        raise NotImplementedError(f"racine inattendue : {tree.data!r}")

    func_trees: list[Tree] = list(tree.children[:-1])
    main_tree: Tree = tree.children[-1]

    funcs: FunctionTable = FunctionTable()
    for ft in func_trees:
        funcs.declare(_build_function(ft))

    main_vars: Tree = main_tree.children[0]
    main_body: Tree = main_tree.children[1]
    main_ret: Tree = main_tree.children[2]

    var_names: list[str] = [_as_token(t).value for t in main_vars.children]
    global_frame: Frame = Frame()
    for i, name in enumerate(var_names):
        global_frame.set(name, argv[i] if i < len(argv) else 0)

    interp: Interpreter = Interpreter(funcs)
    interp.execute(main_body, global_frame)
    result: Valeur = interp.evaluate(main_ret, global_frame)
    if not isinstance(result, int) or isinstance(result, bool):
        raise TypeError(
            f"main doit retourner un entier, reçu {type(result).__name__}"
        )
    return result


def _build_function(node: Tree) -> NanoFunction:
    """Construit un `NanoFunction` à partir d'un noeud `fonction` Lark.

    Forme du noeud : [Token(nom), liste_params?, sequence(corps), expression(retour)].
    Précondition : `node.data == "fonction"` et 3 ou 4 enfants.
    """
    if node.data != "fonction":
        raise NotImplementedError(f"attendu fonction, reçu {node.data!r}")
    name: str = _as_token(node.children[0]).value
    has_params: bool = (
        len(node.children) == 4
        and isinstance(node.children[1], Tree)
        and node.children[1].data == "liste_params"
    )
    if has_params:
        params_node: Tree = node.children[1]  # type: ignore[assignment]
        params: tuple[str, ...] = tuple(
            _as_token(t).value for t in params_node.children
        )
        body: Tree = node.children[2]  # type: ignore[assignment]
        ret: Tree = node.children[3]   # type: ignore[assignment]
    else:
        params = tuple()
        body = node.children[1]  # type: ignore[assignment]
        ret = node.children[2]   # type: ignore[assignment]
    return NanoFunction(name=name, params=params, body=body, return_expr=ret)


class Interpreter:
    """Évaluateur AST. Stateless hors du registre des fonctions.

    Toute la mémoire mutable vit dans les `Frame` passées en paramètre, pas
    dans l'interpréteur lui-même : un même `Interpreter` peut donc exécuter
    plusieurs appels en parallèle conceptuellement (récursivité comprise).
    """

    def __init__(self, funcs: FunctionTable) -> None:
        self.funcs: FunctionTable = funcs

    # ── EXPRESSIONS ───────────────────────────────────────────────────────

    def evaluate(self, node: Tree, frame: Frame) -> Valeur:
        kind: str = node.data
        if kind == "variable":
            return frame.get(_as_token(node.children[0]).value)
        if kind == "entier":
            return int(_as_token(node.children[0]).value)
        if kind == "binaire":
            return self._eval_binaire(node, frame)
        if kind == "appel_fonction":
            return self._eval_appel(node, frame)
        if kind == "acces_index":
            return self._eval_index(node, frame)
        if kind == "longueur":
            return self._eval_longueur(node, frame)
        if kind == "dict_vide":
            return NanoDict()
        if kind == "dict_literal":
            return self._eval_dict_literal(node, frame)
        raise NotImplementedError(f"expression inconnue : {kind!r}")

    def _eval_binaire(self, node: Tree, frame: Frame) -> int:
        left: Valeur = self.evaluate(_as_tree(node.children[0]), frame)
        op: str = _as_token(node.children[1]).value
        right: Valeur = self.evaluate(_as_tree(node.children[2]), frame)
        a: int = _as_int(left, f"opérande gauche de {op!r}")
        b: int = _as_int(right, f"opérande droite de {op!r}")
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            if b == 0:
                raise ZeroDivisionError("division par zéro")
            # Division entière "vers zéro" (sémantique C), pas vers -∞ comme //
            quotient: int = abs(a) // abs(b)
            return quotient if (a < 0) == (b < 0) else -quotient
        if op == "<":
            return 1 if a < b else 0
        if op == ">":
            return 1 if a > b else 0
        if op == "==":
            return 1 if a == b else 0
        if op == "!=":
            return 1 if a != b else 0
        raise NotImplementedError(f"opérateur inconnu : {op!r}")

    def _eval_appel(self, node: Tree, frame: Frame) -> Valeur:
        name: str = _as_token(node.children[0]).value
        args: list[Valeur] = []
        if len(node.children) > 1:
            args_node: Tree = _as_tree(node.children[1])
            args = [self.evaluate(_as_tree(c), frame) for c in args_node.children]
        func: NanoFunction = self.funcs.lookup(name)
        new_frame: Frame = func.bind_args(args)
        self.execute(_as_tree(func.body), new_frame)
        return self.evaluate(_as_tree(func.return_expr), new_frame)

    def _eval_index(self, node: Tree, frame: Frame) -> Valeur:
        name: str = _as_token(node.children[0]).value
        idx: Valeur = self.evaluate(_as_tree(node.children[1]), frame)
        target: Valeur = frame.get(name)
        if isinstance(target, NanoArray):
            return target.get(_as_int(idx, "indice de tableau"))
        if isinstance(target, NanoDict):
            return target.get(_as_int(idx, "clé de dict"))
        raise TypeError(
            f"{name!r} n'est pas indexable (type {type(target).__name__})"
        )

    def _eval_longueur(self, node: Tree, frame: Frame) -> int:
        target: Valeur = self.evaluate(_as_tree(node.children[0]), frame)
        if isinstance(target, NanoArray):
            return target.length()
        if isinstance(target, NanoDict):
            return target.count()
        raise TypeError(
            f"len() attend un tableau ou un dict, reçu {type(target).__name__}"
        )

    def _eval_dict_literal(self, node: Tree, frame: Frame) -> NanoDict:
        paires_node: Tree = _as_tree(node.children[0])
        d: NanoDict = NanoDict()
        for paire in paires_node.children:
            paire_t: Tree = _as_tree(paire)
            k: Valeur = self.evaluate(_as_tree(paire_t.children[0]), frame)
            v: Valeur = self.evaluate(_as_tree(paire_t.children[1]), frame)
            d.set(
                _as_int(k, "clé littérale de dict"),
                _as_int(v, "valeur littérale de dict"),
            )
        return d

    # ── COMMANDES ─────────────────────────────────────────────────────────

    def execute(self, node: Tree, frame: Frame) -> None:
        kind: str = node.data
        if kind == "sequence":
            for child in node.children:
                self.execute(_as_tree(child), frame)
            return
        if kind == "assignation":
            name: str = _as_token(node.children[0]).value
            value: Valeur = self.evaluate(_as_tree(node.children[1]), frame)
            frame.set(name, value)
            return
        if kind == "assignation_index":
            self._exec_assignation_index(node, frame)
            return
        if kind == "pass":
            return
        if kind == "print":
            v: Valeur = self.evaluate(_as_tree(node.children[0]), frame)
            print(v)
            return
        if kind == "if":
            cond: int = _as_int(
                self.evaluate(_as_tree(node.children[0]), frame),
                "condition de if",
            )
            if cond != 0:
                self.execute(_as_tree(node.children[1]), frame)
            return
        if kind == "while":
            cond_node: Tree = _as_tree(node.children[0])
            body_node: Tree = _as_tree(node.children[1])
            while _as_int(
                self.evaluate(cond_node, frame), "condition de while"
            ) != 0:
                self.execute(body_node, frame)
            return
        if kind == "decl_tableau":
            arr_name: str = _as_token(node.children[0]).value
            size: int = _as_int(
                self.evaluate(_as_tree(node.children[1]), frame),
                "taille de tableau",
            )
            frame.set(arr_name, NanoArray(size))
            return
        if kind == "for_in":
            self._exec_for_in(node, frame)
            return
        if kind == "del_index":
            self._exec_del_index(node, frame)
            return
        raise NotImplementedError(f"commande inconnue : {kind!r}")

    def _exec_assignation_index(self, node: Tree, frame: Frame) -> None:
        name: str = _as_token(node.children[0]).value
        idx_val: Valeur = self.evaluate(_as_tree(node.children[1]), frame)
        new_val: Valeur = self.evaluate(_as_tree(node.children[2]), frame)
        target: Valeur = frame.get(name)
        if isinstance(target, NanoArray):
            target.set(
                _as_int(idx_val, "indice de tableau"),
                _as_int(new_val, "valeur de tableau"),
            )
            return
        if isinstance(target, NanoDict):
            target.set(
                _as_int(idx_val, "clé de dict"),
                _as_int(new_val, "valeur de dict"),
            )
            return
        raise TypeError(
            f"{name!r} n'est pas indexable (type {type(target).__name__})"
        )

    def _exec_for_in(self, node: Tree, frame: Frame) -> None:
        k_name: str = _as_token(node.children[0]).value
        d_name: str = _as_token(node.children[1]).value
        body: Tree = _as_tree(node.children[2])
        target: Valeur = frame.get(d_name)
        if not isinstance(target, NanoDict):
            raise TypeError(
                f"for...in attend un dict, reçu {type(target).__name__}"
            )
        for key in target.keys():
            frame.set(k_name, key)
            self.execute(body, frame)

    def _exec_del_index(self, node: Tree, frame: Frame) -> None:
        name: str = _as_token(node.children[0]).value
        key: Valeur = self.evaluate(_as_tree(node.children[1]), frame)
        target: Valeur = frame.get(name)
        if not isinstance(target, NanoDict):
            raise TypeError(
                f"del s'applique uniquement aux dicts, pas à {type(target).__name__}"
            )
        target.delete(_as_int(key, "clé de del"))


# ── helpers de typage strict ──────────────────────────────────────────────


def _as_int(value: Valeur, context: str) -> int:
    """Refuse silencieusement bool et tout non-int. Sinon retourne `value`."""
    if isinstance(value, bool):
        raise TypeError(f"{context} : booléen non supporté")
    if not isinstance(value, int):
        raise TypeError(
            f"{context} : entier attendu, reçu {type(value).__name__}"
        )
    return value


def _as_tree(node: object) -> Tree:
    """Garantit qu'un enfant AST est bien un `Tree` (pas un `Token`)."""
    if not isinstance(node, Tree):
        raise TypeError(f"sous-arbre attendu, reçu {type(node).__name__}")
    return node


def _as_token(node: object) -> Token:
    """Garantit qu'un enfant AST est bien un `Token`."""
    if not isinstance(node, Token):
        raise TypeError(f"token attendu, reçu {type(node).__name__}")
    return node
