function return_42() {
    return 42;
}

function un_argument(a) {
    return a * 2;
}

function max_arguments(a, b, c, d, e, f) {
    return a + b + c + d + e + f;
}

function imbrication_calculs(a, b) {
    return a + b;
}

function fibo(n) {
    r = n;
    if (n > 1) {
        r = fibo(n - 1) + fibo(n - 2);
    }
    return r;
}

main(arg1, arg2) {
        print(return_42());

    print(un_argument(5));

    print(max_arguments(1, 2, 3, 4, 5, 6));

    print(imbrication_calculs(un_argument(10), un_argument(20)));

    print(fibo(6));

    compteur = 0;
    while (compteur != 3) {
        compteur = compteur + 1;
    }
    print(compteur);

    return arg1 + arg2;
}