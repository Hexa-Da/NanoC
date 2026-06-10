main() {
    d = dict();
    d[1] = 100;
    d[2] = 200;
    s = 0;
    for (k in d) {
        s = s + d[k];
    }
    print(s);  
    return 0;
}