function add(a, b) {
    return a + b;
}

function twice(x) {
    return x * 2;
}

main() {
    int t[3];
    t[0] = 10;
    t[1] = 20;
    print(t[0] + t[1]);
    print(len(t));

    d = dict();
    d[1] = 100;
    d[2] = 200;
    print(d[1]);
    print(len(d));

    print(add(2, 3));
    print(add(twice(2), twice(3)));

    return 0;
}
