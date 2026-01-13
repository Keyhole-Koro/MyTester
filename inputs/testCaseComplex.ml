typedef struct {
    int val;
} Data;

Data g_data;

int get_val() {
    return 100;
}

Data* get_ptr() {
    return &g_data;
}

int main() {
    g_data.val = 0;
    
    int x = 0;
    
    // 1. Function return value
    int res1 = case x of {
        0 -> get_val();
        _ -> 0;
    };
    
    // 2. Case returning pointer, used in assignment LHS (via arrow)
    // Parentheses might be needed or not, depending on precedence, but (...) is safe.
    (case x of { 
        0 -> get_ptr(); 
        _ -> (Data*)0; 
    })->val = 300;

    return res1 + g_data.val; // 100 + 300 = 400
}
