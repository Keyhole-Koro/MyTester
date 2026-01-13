typedef struct {
    int val;
} Data;

Data g_data;
Data *addr_g_data;

int main() {
    g_data.val = 10;
    addr_g_data = &g_data;
    int x = 10;
    
    // Case where key is a struct member access expression
    int res = case x of {
        addr_g_data->val -> 100;
        _ -> 200;
    };
    
    return res;
}
