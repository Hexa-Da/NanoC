"""Dev A — Fonctions utilisateur et portées d'exécution.

À implémenter par le Dev A. Ce module est autonome : aucun import des
autres `*_impl.py`.

API attendue par `interp.py` :
  - NanoFunction(name, params, body, return_expr)  : définition immuable
  - NanoFunction.bind_args(args) -> Frame         : lie paramètres ← args
  - Frame.get(name) / Frame.set(name, value)      : variables locales
  - FunctionTable.declare / .lookup / .has        : registre des fonctions

Modèle de portée (simple, style C) :
  - une Frame pour le main (variables + args CLI)
  - une nouvelle Frame par appel de fonction
  - pas de variables libres : tout passe par paramètres ou locales

Les champs `body` et `return_expr` sont des noeuds AST (type `Any`) :
`interp.py` les évalue ; tu n'as pas besoin d'importer Lark ici.

Tests isolés (exemple) :
  python -c "from func_impl import Frame; f = Frame(); f.set('x', 3); print(f.get('x'))"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NanoFunction:
    """Définition d'une fonction utilisateur (objet immuable)."""

    name: str
    params: tuple[str, ...]
    body: Any
    return_expr: Any

    def bind_args(self, args: list[Any]) -> "Frame":
        """Crée la Frame d'un appel : chaque paramètre ← valeur correspondante.

        Précondition : `len(args) == len(self.params)`.
        Lève `TypeError` si l'arité ne correspond pas.
        """
        raise NotImplementedError("Dev A — NanoFunction.bind_args à implémenter")


@dataclass
class Frame:
    """Portée locale d'une exécution (main ou appel de fonction)."""

    vars: dict[str, Any] = field(default_factory=dict)

    def get(self, name: str) -> Any:
        """Lit `name`. Lève `NameError` si la variable n'existe pas."""
        raise NotImplementedError("Dev A — Frame.get à implémenter")

    def set(self, name: str, value: Any) -> None:
        """Écrit `name = value` (crée ou écrase)."""
        raise NotImplementedError("Dev A — Frame.set à implémenter")


class FunctionTable:
    """Registre global des fonctions utilisateur, indexé par nom."""

    def __init__(self) -> None:
        self._functions: dict[str, NanoFunction] = {}

    def declare(self, func: NanoFunction) -> None:
        """Enregistre une fonction. Lève `NameError` si le nom existe déjà."""
        raise NotImplementedError("Dev A — FunctionTable.declare à implémenter")

    def lookup(self, name: str) -> NanoFunction:
        """Retourne la fonction `name`. Lève `NameError` si inconnue."""
        raise NotImplementedError("Dev A — FunctionTable.lookup à implémenter")

    def has(self, name: str) -> bool:
        """`True` si une fonction `name` est enregistrée."""
        raise NotImplementedError("Dev A — FunctionTable.has à implémenter")
