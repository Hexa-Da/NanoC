# nanoC — mini compilateur (fonctions, dictionnaires, tableaux)

On compile un petit langage façon C (`source.c`) vers de l'assembleur **x86-64** (NASM), assemblé et lié pour **Linux**.

```
source.c  ── nanoC.py ──►  resultat.asm  ── nasm ──►  resultat.o  ── gcc ──►  ./resultat
```

## Cible et prérequis

- **Linux x86_64 uniquement** (`nasm -f elf64`, `gcc -no-pie`, ABI System V).
- Python 3 + [lark](https://github.com/lark-parser/lark), `nasm`, `gcc`.

Installation des dépendances Python :

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Compiler et exécuter

```bash
./script.sh            # compile source.c puis lance ./resultat
./script.sh 3 7 42     # passe des arguments aux paramètres du main
.venv/bin/python nanoC.py --pp   # affiche le programme reformaté (debug / cours)
```

Le `return` du `main` devient le **code de sortie** ; chaque `print(e);`
affiche un entier sur sa propre ligne.

## Architecture (un fichier par développeur)

| Fichier             | Rôle                                                   | Responsable |
| ------------------- | ------------------------------------------------------ | ----------- |
| `nanoC.py`          | grammaire, orchestration, `pp_programme`, `--pp`       | commun      |
| `symboltable.py`    | types des variables + labels ASM + zone `.data`        | commun      |
| `codegen_base.py`   | façade (réexporte les modules ci-dessous)              | commun      |
| `codegen_hub.py`    | `Gen` / `Pp` + dispatch assembleur                     | commun      |
| `codegen_lang.py`   | entiers, opérateurs, if/while/print, argv              | commun      |
| `codegen_analyse.py`| `build_symbols` (pré-passe symtab)                     | commun      |
| `codegen_debug.py`  | pretty-print `pp_*` (`--pp`)                           | commun      |
| `codegen_ast.py`    | helpers lecture AST                                    | commun      |
| `codegen_func.py`   | fonctions (pile, appels, return)                       | Dev A       |
| `codegen_dict.py`   | dictionnaires (balayage linéaire)                      | Dev B       |
| `codegen_array.py`  | tableaux 1D                                            | Dev C       |
| `squelette.asm`     | gabarit assembleur (placeholders)                      | commun      |
| `SYNTAXE.md`        | syntaxe, exemples, périmètre v1                        | commun      |

Règle d'isolation : `codegen_base` importe les 3 modules de feature ; ces
modules **ne s'importent pas entre eux** (ils reçoivent un contexte `gen`).

## Modèle mémoire (sans runtime C)

Tout est statique, en `.data`, capacité fixe `symboltable.py` :

- **tableau** `t` : `arr_t` (entiers) + `arrlen_t` (longueur).
- **dict** `d` : `dk_d`/`dv_d` (clés/valeurs), `du_d` (slot occupé),
  `dcount_d` (prochain ajout), `dsize_d` (taille). Recherche par balayage.
- **fonction** : paramètres et locales sur la pile (`[rbp - 8*i]`).

## Fonctionnalités (v1)

Voir `SYNTAXE.md` pour les exemples détaillés et le périmètre exact.

- Fonctions int→int (jusqu'à 6 paramètres), récursion et appels imbriqués
  dans les arguments (`f(g(x), y)`).
- Dictionnaires int→int : `dict()`, `{..}`, `d[k]`, `d[k]=`, `for (k in d)`,
  `del d[k]`, `len(d)`.
- Tableaux 1D d'entiers : `int t[E];`, `t[i]`, `t[i]=`, `len(t)`.

Hors périmètre v1 : multi-dimensions, chaînes, `else`, macOS/Windows.

## Note de test

La génération de `resultat.asm` (Python) et l'assemblage `nasm -f elf64` sont
indépendants de l'OS hôte. L'**exécution** nécessite Linux x86_64 (binaire ELF).

Lors de l'assemblage, NASM peut afficher un avertissement du type
`implicit DEFAULT ABS is deprecated` sur la ligne `main:` du squelette.
C'est bénin avec `-no-pie` et n'empêche pas la génération du binaire.
