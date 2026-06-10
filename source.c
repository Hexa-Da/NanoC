main() {
    d = dict();
    d[1] = 100;
    d[2] = 200;
    print(len(d));
    del d[1];
    print(len(d));
    print(d[1]);
    return 0;
}