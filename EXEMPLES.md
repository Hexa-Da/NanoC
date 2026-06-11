# EXEMPLES.md — Programmes NanoC valides et contre-exemples

Ce fichier documente des programmes corrects et incorrects en NanoC.
Pour chaque contre-exemple, la raison de l'invalidité est expliquée simplement.

---

## Programmes valides

### 1. Entiers et opérations de base

```c
main() {
    x = 3 + 4 * 2;
    print(x);        /* affiche 14 */
    return 0;
}
```

### 2. Condition et boucle

```c
main() {
    i = 0;
    while (i < 5) {
        print(i);
        i = i + 1;
    }
    return 0;
}
```

### 3. Tableau statique

```c
main() {
    int t[4];        /* alloue 4 cases, toutes à 0 */
    t[0] = 10;
    t[1] = 20;
    print(t[0] + t[1]);   /* 30 */
    print(len(t));         /* 4  */
    return 0;
}
```

### 4. Dictionnaire

```c
main() {
    d = dict();
    d[1] = 100;
    d[2] = 200;
    print(d[1]);           /* 100 */
    print(len(d));         /* 2   */

    s = 0;
    for (k in d) {
        s = s + d[k];
    }
    print(s);              /* 300 */

    del d[1];
    print(len(d));         /* 1   */
    return 0;
}
```

### 5. Dictionnaire littéral

```c
main() {
    d = {7:70, 8:80, 9:90};
    print(d[8]);    /* 80 */
    return 0;
}
```

### 6. Fonction (entiers uniquement)

```c
function add(a, b) {
    return a + b;
}

function fact(n) {
    r = 1;
    if (n > 1) {
        r = n * fact(n - 1);
    }
    return r;
}

function twice(x) {
    return x * 2;
}

main() {
    print(add(2, 3));                        /* 5   */
    print(add(twice(2), twice(3)));            /* 10  : appels imbriqués dans les args */
    print(fact(5));                          /* 120 */
    return 0;
}
```

---

## Contre-exemples annotés

> Pour chaque exemple invalide, le compilateur lève une `ErreurCompilation`
> avec un message lisible, sans traceback Python.

---

### CE-1 : `d + 4` — dict utilisé dans une opération arithmétique

```c
main() {
    d = dict();
    x = d + 4;    /* ERREUR */
    return 0;
}
```

**Pourquoi ?**
L'opérateur `+` attend deux entiers. `d` est un dictionnaire, pas un entier.
Un dictionnaire est une structure complexe en mémoire ; lui appliquer `+`
n'a pas de sens et produirait un résultat aléatoire.

**Message du compilateur :**
```
Erreur de compilation : type incorrect (opérande gauche de '+') : attendu 'int', obtenu 'dict'
```

---

### CE-2 : `d[d]` — indice de type dict

```c
main() {
    d = dict();
    x = d[d];    /* ERREUR */
    return 0;
}
```

**Pourquoi ?**
L'indice d'un accès `t[i]` ou `d[k]` doit être un entier.
Utiliser un dictionnaire comme clé n'est pas supporté en NanoC v1 :
les clés sont toujours des entiers.

**Message du compilateur :**
```
Erreur de compilation : type incorrect (indice de 'd') : attendu 'int', obtenu 'dict'
```

---

### CE-3 : `d[3] = t` — valeur de type tableau

```c
main() {
    int t[5];
    d = dict();
    d[3] = t;    /* ERREUR */
    return 0;
}
```

**Pourquoi ?**
Les dictionnaires et tableaux NanoC ne stockent que des entiers.
Affecter un tableau entier comme valeur n'est pas possible : il faudrait
copier toute la mémoire du tableau, ce qui n'est pas implémenté.

**Message du compilateur :**
```
Erreur de compilation : type incorrect (valeur assignée à 'd[...]') : attendu 'int', obtenu 'array'
```

---

### CE-4 : plus de 6 paramètres de fonction

```c
function f(a, b, c, d, e, f, g) {    /* ERREUR : 7 paramètres */
    return a + b;
}
```

**Pourquoi ?**
L'ABI x86-64 Linux (System V AMD64) passe les 6 premiers arguments entiers
dans les registres `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9`.
Au-delà, les arguments sont passés sur la pile, ce qui complique
significativement la gestion du cadre de pile (stack frame).
NanoC v1 se limite à 6 paramètres pour rester simple et pédagogique.

**Message du compilateur :**
```
Erreur de compilation : fonction 'f' : trop de paramètres (7 > 6)
```

---

### CE-5 : tableau multi-dimensionnel `int t[2][3]`

```c
main() {
    int t[2][3];    /* ERREUR */
    return 0;
}
```

**Pourquoi ?**
NanoC v1 ne supporte que les tableaux 1D.
Un tableau 2D nécessiterait soit un calcul d'adresse `i*colonnes + j`,
soit des pointeurs de pointeurs, ce qui sort du périmètre du projet.

**Message du compilateur :**
```
Erreur de syntaxe : la grammaire n'accepte pas int t[E][F]
```

---

### CE-6 : déclaration de tableau dans une fonction

```c
function f(n) {
    int t[5];       /* ERREUR */
    t[0] = n;
    return t[0];
}
```

**Pourquoi ?**
Les tableaux NanoC sont alloués statiquement dans la section `.data` de
l'assembleur. Ils doivent donc être déclarés dans le `main`, où la taille
est connue à la compilation. Dans une fonction, les variables sont allouées
sur la pile d'appel (frame) : implémenter un tableau sur la pile nécessite
`alloca` ou un cadre de taille variable, hors périmètre v1.

**Message du compilateur :**
```
Erreur de compilation : tableaux/dicts seulement dans main en v1 (pas dans une fonction)
```

---

### CE-7 : `print` d'un tableau ou d'un dict

```c
main() {
    int t[3];
    print(t);    /* ERREUR */

    d = dict();
    print(d);    /* ERREUR */
    return 0;
}
```

**Pourquoi ?**
`print` utilise `printf("%lld", valeur)` et n'affiche qu'un seul entier 64 bits.
Afficher un tableau ou un dictionnaire nécessiterait une boucle explicite.

**Message du compilateur :**
```
Erreur de compilation : type incorrect (argument de print) : attendu 'int', obtenu 'array'
```

---

### CE-8 : `len` sur un entier

```c
main() {
    x = 42;
    print(len(x));    /* ERREUR */
    return 0;
}
```

**Pourquoi ?**
`len` est défini uniquement pour les tableaux et les dictionnaires.
Un entier scalaire n'a pas de longueur.

**Message du compilateur :**
```
Erreur de compilation : len('x') interdit : 'x' est un entier, pas un tableau/dict
```

---

## Récapitulatif des règles de types

| Opération         | Type attendu (opérandes) | Type produit |
|-------------------|--------------------------|--------------|
| `a + b`, `a * b`  | int, int                 | int          |
| `a < b`, `a == b` | int, int                 | int (0 ou 1) |
| `t[i]`            | indice : int             | int          |
| `d[k]`            | clé : int                | int          |
| `t[i] = v`        | indice : int, valeur : int | —          |
| `d[k] = v`        | clé : int, valeur : int  | —            |
| `len(x)`          | array ou dict            | int          |
| `print(e)`        | int                      | —            |
| appel fonction    | args : int               | int          |
