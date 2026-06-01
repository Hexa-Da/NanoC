"""Table des symboles du compilateur nanoC (couche partagée).

Rôle :
  1. Mémoriser le TYPE de chaque variable globale du `main` :
     "int" | "array" | "dict". C'est ce qui permet, plus tard, de choisir
     le bon code pour `t[i]` (tableau) ou `d[k]` (dictionnaire) — le conseil
     prof du "left hand side".
  2. Mémoriser les fonctions de l'utilisateur (paramètres + corps + retour),
     avec l'emplacement sur la pile de chaque variable locale.
  3. Fabriquer de façon centralisée tous les NOMS DE LABELS assembleur, pour
     que `emit_data` (déclaration mémoire) et les modules de génération
     utilisent exactement les mêmes étiquettes.

Modèle mémoire (sans runtime C) :
  - variable entière globale `x`        -> label `gv_x: dq 0`
  - tableau `t` (capacité fixe CAP)     -> `arr_t: times CAP dq 0`
                                           `arrlen_t: dq 0` (longueur réelle)
  - dictionnaire `d` (balayage linéaire) -> `dk_d`  (clés)
                                            `dv_d`  (valeurs)
                                            `du_d`  (1 = slot occupé, 0 = libre)
                                            `dcount_d` (indice du prochain ajout)
                                            `dsize_d`  (nombre d'entrées vivantes)

Aucune dépendance vers les modules `codegen_*` : c'est une brique de base.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

VarType = Literal["int", "array", "dict"]

# Capacité maximale (en nombre d'entiers) d'un tableau ou d'un dict.
# Fixe car on n'a pas d'allocation dynamique (pas de runtime C en v1).
CAP: int = 1024

# Registres d'arguments de l'ABI System V AMD64 (Linux), dans l'ordre.
ARG_REGS: tuple[str, ...] = ("rdi", "rsi", "rdx", "rcx", "r8", "r9")
MAX_ARGS: int = len(ARG_REGS)


@dataclass
class FuncInfo:
    """Description d'une fonction utilisateur.

    Invariants :
      - `params` est un préfixe de `locals` (les paramètres sont les premières
        variables locales, dans l'ordre).
      - chaque nom de `locals` est unique.
      - une variable locale d'indice `i` est stockée à `[rbp - 8*(i+1)]`.
    """

    name: str
    params: list[str]
    locals: list[str]
    body: object          # noeud AST `sequence`
    ret: object           # noeud AST de l'expression de retour

    def offset(self, name: str) -> int:
        """Décalage pile (octets positifs) d'une variable locale.

        Précondition : `name in self.locals`.
        Retour : entier d tel que la variable est en `[rbp - d]`.
        """
        if name not in self.locals:
            raise NameError(
                f"variable locale inconnue dans {self.name!r} : {name!r}"
            )
        return 8 * (self.locals.index(name) + 1)

    def frame_size(self) -> int:
        """Taille de pile à réserver (octets), alignée sur 16 (ABI SysV)."""
        raw: int = 8 * len(self.locals)
        return (raw + 15) // 16 * 16


class SymbolTable:
    """Registre des variables globales, des fonctions et des labels ASM."""

    def __init__(self) -> None:
        self.CAP: int = CAP
        self._globals: dict[str, VarType] = {}
        self._init_order: list[str] = []          # params du main, dans l'ordre
        self._functions: dict[str, FuncInfo] = {}
        self._counter: int = 0

    # ── variables globales ────────────────────────────────────────────────

    def declare_global(self, name: str, vtype: VarType) -> None:
        """Déclare (ou confirme) une variable globale et son type.

        Règle de priorité si le nom existe déjà : "array" et "dict" ne peuvent
        pas être réduits en "int". Un conflit array<->dict est une erreur
        (refus explicite plutôt que code faux silencieux).
        """
        prev: VarType | None = self._globals.get(name)
        if prev is None or prev == "int":
            self._globals[name] = vtype
            return
        if prev == vtype:
            return
        if vtype == "int":
            return  # on garde le type composite déjà connu
        raise TypeError(
            f"type incohérent pour {name!r} : déjà {prev!r}, redéclaré {vtype!r}"
        )

    def declare_main_param(self, name: str) -> None:
        """Déclare un paramètre du main (entier, initialisé depuis argv)."""
        self.declare_global(name, "int")
        if name not in self._init_order:
            self._init_order.append(name)

    def is_global(self, name: str) -> bool:
        return name in self._globals

    def type_of(self, name: str) -> VarType:
        """Type d'une variable globale. Lève `NameError` si inconnue."""
        if name not in self._globals:
            raise NameError(f"variable globale inconnue : {name!r}")
        return self._globals[name]

    def init_params(self) -> list[str]:
        return list(self._init_order)

    # ── fonctions ─────────────────────────────────────────────────────────

    def declare_function(self, info: FuncInfo) -> None:
        if info.name in self._functions:
            raise NameError(f"fonction déjà déclarée : {info.name!r}")
        self._functions[info.name] = info

    def lookup_function(self, name: str) -> FuncInfo:
        if name not in self._functions:
            raise NameError(f"fonction inconnue : {name!r}")
        return self._functions[name]

    # ── labels assembleur (source unique de vérité) ───────────────────────

    def gv(self, name: str) -> str:
        return f"gv_{name}"

    def arr_data(self, name: str) -> str:
        return f"arr_{name}"

    def arr_len(self, name: str) -> str:
        return f"arrlen_{name}"

    def dk(self, name: str) -> str:
        return f"dk_{name}"

    def dv(self, name: str) -> str:
        return f"dv_{name}"

    def du(self, name: str) -> str:
        return f"du_{name}"

    def dcount(self, name: str) -> str:
        return f"dcount_{name}"

    def dsize(self, name: str) -> str:
        return f"dsize_{name}"

    def func_label(self, name: str) -> str:
        return f"func_{name}"

    def new_label(self, prefix: str) -> str:
        """Renvoie un label unique du genre `prefix_N` (N croissant)."""
        n: int = self._counter
        self._counter += 1
        return f"{prefix}_{n}"

    # ── émission de la zone .data ─────────────────────────────────────────

    def emit_data(self) -> str:
        """Génère les déclarations mémoire de toutes les variables globales."""
        lines: list[str] = []
        for name, vtype in self._globals.items():
            if vtype == "int":
                lines.append(f"{self.gv(name)}: dq 0")
            elif vtype == "array":
                lines.append(f"{self.arr_data(name)}: times {self.CAP} dq 0")
                lines.append(f"{self.arr_len(name)}: dq 0")
            elif vtype == "dict":
                lines.append(f"{self.dk(name)}: times {self.CAP} dq 0")
                lines.append(f"{self.dv(name)}: times {self.CAP} dq 0")
                lines.append(f"{self.du(name)}: times {self.CAP} dq 0")
                lines.append(f"{self.dcount(name)}: dq 0")
                lines.append(f"{self.dsize(name)}: dq 0")
            else:  # pragma: no cover - garde-fou
                raise NotImplementedError(f"type global inconnu : {vtype!r}")
        return "\n".join(lines) + "\n"
