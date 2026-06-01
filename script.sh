#!/bin/bash
# Compile et exécute un programme nanoC (cible : Linux x86_64).
# Étapes : génération de l'assembleur -> assemblage NASM -> édition de liens.
set -e

# Utilise le python du venv s'il existe, sinon python3 du système.
if [ -x ".venv/bin/python" ]; then
    PY=".venv/bin/python"
else
    PY="python3"
fi

"$PY" nanoC.py                     # source.c -> resultat.asm
nasm -f elf64 resultat.asm         # resultat.asm -> resultat.o
gcc -no-pie resultat.o -o resultat # édition de liens (libc : printf, atoi)
./resultat "$@"                    # exécute (args -> paramètres du main)
