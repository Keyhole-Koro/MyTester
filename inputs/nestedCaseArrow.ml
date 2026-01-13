typedef struct {
    int v;
} Data;

Data d;
Data *p;

int main() {
    d.v = 5;
    p = &d;

    int x = 1;
    int res = case x of {
        1 -> (case p->v of { 5 -> 10; _ -> 0; });
        _ -> 0;
    };

    return res;
}
