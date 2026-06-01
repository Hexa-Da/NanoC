# SYNTAXE nanoC — phase brainstorming (v1)

Document de référence d'équipe. À lire avant de coder.

## Périmètre v1 (ce qu'on fait maintenant)

- **Entiers uniquement** partout (clés, valeurs, paramètres, retours).
- **Cible unique** : Linux x86_64 (`nasm -f elf64` + `gcc -no-pie`).
- **Pas de runtime C** : tableaux et dictionnaires sont des zones mémoire
  réservées directement dans l'assembleur généré (`.data`).
- **Tableaux 1D** seulement.
- Trois features, **un fichier par développeur** :
  - Dev A → `codegen_func.py` (fonctions)
  - Dev B → `codegen_dict.py` (dictionnaires)
  - Dev C → `codegen_array.py` (tableaux)

## Hors périmètre (v2 / bonus, documenté mais pas codé)

- Tableaux multi-dimensionnels et sous-tableaux de tailles différentes.
- Chaînes de caractères, flottants.
- `else`, opérateurs booléens.
- macOS / Windows.
- Table de hachage pour les dicts (on fait un **balayage linéaire** simple).

## Forme générale d'un programme

```
function nom(p1, p2) { ... return expr; }   # 0..N fonctions
main(x, y, z) { ... return expr; }           # un seul main
```

- `main(x, y, z)` : les paramètres sont initialisés depuis les arguments de la
  ligne de commande (`./resultat 3 7 42` → x=3, y=7, z=42), 0 si absent.
- Le `return` du `main` devient le **code de sortie** du programme.

## Règle clé : le type est porté par la variable (conseil prof "LHS")

`x[i]` ne suffit pas à savoir si c'est un tableau ou un dict. La **table des
symboles** (`symboltable.py`) mémorise le type de chaque variable à sa
déclaration :

- `int t[E];`        → `t` est un **tableau**
- `d = dict();`      → `d` est un **dict**
- `d = {1:10};`      → `d` est un **dict**
- tout le reste      → **entier**

Ensuite, pour `t[i]` vs `d[k]`, le compilateur regarde le type de `t`/`d`.

## Feature A — Fonctions

Valide :

```
function add(a, b) { return a + b; }
function fact(n) {
    r = 1;
    if (n > 1) { r = n * fact(n - 1); }
    return r;
}
```

- Nombre arbitraire de fonctions, jusqu'à **6 paramètres** (limite ABI v1).
- Paramètres et retour : **entiers**.
- Récursivité autorisée (pile).
- Variables internes : locales à la fonction (sur la pile).

Invalide v1 :

- `function f() { int t[3]; ... }` → pas de tableau/dict dans une fonction.
- Plus de 6 paramètres.

## Feature B — Dictionnaires (`int → int`)

Valide :

```
d = dict();
d[3] = 4;
k = d[3];
d = {3:4, 4:5};
for (k in d) { del d[k]; }
print(len(d));
```

- `len(d)` = nombre d'entrées présentes.
- `del d[k]` sur clé absente : ne fait rien (pas de crash).
- `d[k]` sur clé absente : renvoie 0 (v1, pas d'erreur).

## Feature C — Tableaux (1D, entiers)

Valide :

```
int t[5];
t[0] = 1;
t[2] = 4;
print(t[2]);
print(len(t));
i = 0;
while (i < len(t)) { i = i + 1; }
```

- `int t[E];` : `E` est une expression (longueur), tableau initialisé à 0.
- `len(t)` = longueur déclarée.
- Capacité maximale fixe par tableau (voir `CAP` dans `symboltable.py`).

Invalide v1 :

- `int t[2][3];` (multi-dim) → v2.

## Grammaire (annotée)

Voir `nanoC.py`. Points ajoutés à la base :

- `programme : fonction* main`
- `bloc : commande*` (suite de commandes)
- expressions : `appel_fonction`, `acces_index`, `len`, `dict()`, `{...}`
- commandes : `assignation_index`, `int t[E];`, `for (k in d)`, `del d[k]`

## Opérateurs

`+  -  *  /  <  >  ==  !=` — division entière, comparaisons renvoient 0 ou 1.
