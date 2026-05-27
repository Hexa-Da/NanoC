# NanoC

Mini-interpréteur pédagogique d'un langage style C/Python.
Pipeline : `source.c` → grammaire Lark → AST → évaluation Python.
Aucune dépendance native, aucune compilation. 
Tourne sur macOS / Linux / Windows.

Le projet est découpé pour **3 développeurs** travaillant en parallèle :

| Dev | Module | Responsabilité |
|---|---|---|
| **A** | `func_impl.py` | Fonctions utilisateur, paramètres, frames d'appel |
| **B** | `dict_impl.py` | Dictionnaire `int → int` |
| **C** | `array_impl.py` | Tableau d'entiers de taille fixe |

Chaque module est **autonome** (aucune dépendance entre eux). C'est `interp.py`
qui orchestre les trois.

## Fonctionnalités

- **Entiers** uniquement (signés, taille arbitraire — Python)
- **Tableaux** : `int t[N];`, `t[i]`, `t[i] = v;`, `len(t)`
- **Dictionnaires** `int → int` : `dict()`, `{1:10, 2:20}`, `d[k]`, `d[k] = v;`, `del d[k];`, `for (k in d) { ... }`
- **Fonctions** : déclaration, appel, récursivité
- **Contrôle** : `if`, `while`, `pass`
- **Opérateurs** : `+ - * / < > == !=`

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate     # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Exécution

Le programme est **toujours** lu depuis `source.c` à la racine du dépôt.

```bash
python nanoC.py              # lit source.c, main(x,y,z) initialisé à 0
python nanoC.py 3 7 42       # idem, avec x=3, y=7, z=42
```

## Structure du projet

| Fichier | Rôle |
|---|---|
| `nanoC.py` | Grammaire Lark, lecture de `source.c`, arguments du `main` |
| `interp.py` | Évaluateur AST, dispatch vers les 3 modules |
| `array_impl.py` | **Dev C** — `NanoArray` (tableau from scratch) |
| `dict_impl.py` | **Dev B** — `NanoDict` (hash table open-addressing) |
| `func_impl.py` | **Dev A** — `NanoFunction`, `Frame`, `FunctionTable` |
| `source.c` | Programme à exécuter |

## Architecture (qui appelle qui)

```
nanoC.py  ──parse──►  AST  ──run──►  interp.py
                                       │
                  ┌────────────────────┼────────────────────┐
                  ▼                    ▼                    ▼
            array_impl.py        dict_impl.py         func_impl.py
              NanoArray            NanoDict            NanoFunction
                                                      Frame
                                                      FunctionTable
```

- Les trois `*_impl.py` n'importent **rien** les uns des autres.
- `interp.py` est le seul à connaître les trois.
- Cela permet à chaque dev de tester son module indépendamment
  (par exemple : `python -c "from dict_impl import NanoDict; ..."`).

## Forme d'un programme

```
function fact(n) {
    r = 1;
    if (n > 1) { r = n * fact(n - 1); }
    return r;
}

main(x, y, z) {
    int t[5];
    t[0] = 1; t[1] = 2; t[2] = 3; t[3] = 4; t[4] = 5;
    d = {1: 10, 2: 20};
    d[3] = 30;
    print(fact(5));
    print(t[2]);
    print(d[3]);
    return 0;
}
```

Le `main(x, y, z)` déclare les variables globales du programme ; elles sont
initialisées avec les arguments CLI (zéro si non fournis).

