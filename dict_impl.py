"""Dev B — Dictionnaire `int -> int` from scratch.

À implémenter par le Dev B. Ce module est autonome : aucun import des
autres `*_impl.py`.

API attendue par `interp.py` :
  - NanoDict()          : dict vide
  - .set(key, value)    : insère ou met à jour
  - .get(key)           : lit la valeur → KeyError si absente
  - .delete(key)        : supprime → KeyError si absente
  - .count()            : nombre d'entrées (pour len(d))
  - .keys()             : itérateur sur les clés (pour for (k in d))

Piste d'implémentation : table de hachage à adressage ouvert, sondage
linéaire. Trois états par slot : EMPTY / OCCUPIED / TOMBSTONE (pour del).
Redimensionner quand la charge dépasse ~75 %.

Constantes suggérées (tu peux les utiliser ou non) :
  _EMPTY = 0, _OCCUPIED = 1, _TOMBSTONE = 2
  capacité initiale = 8 (puissance de 2)

Tests isolés (exemple) :
  python -c "from dict_impl import NanoDict; d = NanoDict(); d.set(1, 10); print(d.get(1))"
"""

from __future__ import annotations

from typing import Iterator


class NanoDict:
    """Table de hachage `int -> int` à adressage ouvert."""

    def __init__(self) -> None:
        """Crée un dictionnaire vide."""
        raise NotImplementedError("Dev B — NanoDict.__init__ à implémenter")

    def set(self, key: int, value: int) -> None:
        """Insère ou met à jour `key -> value`.

        Précondition : `key` et `value` sont des `int`.
        """
        raise NotImplementedError("Dev B — NanoDict.set à implémenter")

    def get(self, key: int) -> int:
        """Retourne la valeur associée à `key`.

        Lève `KeyError` si la clé n'existe pas (pas de valeur par défaut).
        """
        raise NotImplementedError("Dev B — NanoDict.get à implémenter")

    def delete(self, key: int) -> None:
        """Supprime `key`. Lève `KeyError` si absente."""
        raise NotImplementedError("Dev B — NanoDict.delete à implémenter")

    def count(self) -> int:
        """Nombre d'entrées effectivement présentes."""
        raise NotImplementedError("Dev B — NanoDict.count à implémenter")

    def keys(self) -> Iterator[int]:
        """Itère sur les clés présentes.

        Conseil : renvoyer une copie des clés pour que `del d[k]` dans un
        `for (k in d)` ne corrompe pas l'itération.
        """
        raise NotImplementedError("Dev B — NanoDict.keys à implémenter")
