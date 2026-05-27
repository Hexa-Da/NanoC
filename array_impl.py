"""Dev C — Tableaux d'entiers (taille fixe, from scratch).

À implémenter par le Dev C. Ce module est autonome : aucun import des
autres `*_impl.py`.

API attendue par `interp.py` :
  - NanoArray(size)     : alloue `size` entiers initialisés à 0
  - .get(index)         : lit t[i]  → IndexError si hors bornes
  - .set(index, value)  : écrit t[i] = value
  - .length()           : retourne la taille fixe N

Conseil : un tableau = une liste Python `list[int]` de longueur N + une
variable `_size` mémorisée. Vérifier `0 <= index < _size` à chaque accès.

Tests isolés (exemple) :
  python -c "from array_impl import NanoArray; t = NanoArray(3); t.set(0, 42); print(t.get(0))"
"""

from __future__ import annotations


class NanoArray:
    """Tableau d'entiers de taille fixe.

    Invariant visé : `len(self._data) == self._size` à tout instant.
  """

    def __init__(self, size: int) -> None:
        """Alloue un tableau de `size` entiers, tous initialisés à 0.

        Précondition : `size` est un entier >= 0.
        Lève `ValueError` si `size` est négatif.
        Lève `TypeError` si `size` n'est pas un int.
        """
        raise NotImplementedError("Dev C — NanoArray.__init__ à implémenter")

    def get(self, index: int) -> int:
        """Lit l'élément à l'indice `index`.

        Précondition : `0 <= index < self._size`.
        Lève `IndexError` sinon.
        """
        raise NotImplementedError("Dev C — NanoArray.get à implémenter")

    def set(self, index: int, value: int) -> None:
        """Écrit `value` à l'indice `index`.

        Précondition : `0 <= index < self._size` et `value` est un `int`.
        """
        raise NotImplementedError("Dev C — NanoArray.set à implémenter")

    def length(self) -> int:
        """Retourne la longueur (capacité fixe) du tableau."""
        raise NotImplementedError("Dev C — NanoArray.length à implémenter")
