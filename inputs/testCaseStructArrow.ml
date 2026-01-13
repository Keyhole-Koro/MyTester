typedef struct {
    int val;
} Data;

int main() {
    Data d;
    Data *p;
    d.val = 42;
    p = &d;
    
    int x = 1;
    int res = case x of {
        0 -> 0;
        1 -> p->val;
        _ -> -1;
    };
    return res;
}
