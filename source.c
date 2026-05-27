function fact(n) {
    r = 1;
    if (n > 1) { r = n * fact(n - 1); }
    return r;
}

function somme_tableau(t) {
    s = 0;
    i = 0;
    while (i < len(t)) {
        s = s + t[i];
        i = i + 1;
    }
    return s;
}

main(x, y, z) {
    int t[5];
    t[0] = 1;
    t[1] = 2;
    t[2] = 3;
    t[3] = 4;
    t[4] = 5;

    d = {1: 10, 2: 20};
    d[3] = 30;
    del d[1];

    print(fact(5));
    print(somme_tableau(t));
    print(d[3]);
    print(len(d));
    return 0;
}
