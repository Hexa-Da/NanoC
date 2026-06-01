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

main(x) {
    print(add(2, 3));
    print(fact(5));

    int t[5];
    i = 0;
    while (i < len(t)) {
        t[i] = i * i;
        i = i + 1;
    }
    print(t[4]);
    print(len(t));

    d = dict();
    d[3] = 4;
    d[5] = 9;
    print(d[3]);
    print(len(d));

    d = {7:70, 8:80, 9:90};
    print(len(d));
    print(d[8]);

    s = 0;
    for (k in d) {
        s = s + d[k];
    }
    print(s);

    del d[8];
    print(len(d));

    return 0;
}
