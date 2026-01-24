int g_x = 10;
int g_y = -5;
char g_c = 'A';
char g_d = 100;

int update_globals() {
    g_x = g_x + g_y; // 10 + (-5) = 5
    g_c = g_c + 1;   // 'A' (65) + 1 = 'B' (66)
    return g_x;
}

int main() {
    // Check initial values
    if (g_x != 10) return 1;
    if (g_y != -5) return 2;
    if (g_c != 'A') return 3;
    
    // Modify globals
    int val = update_globals();
    
    // Check modified values
    if (val != 5) return 4;
    if (g_x != 5) return 5;
    if (g_c != 'B') return 6;
    
    // Test mixing char and int globals
    int res = g_d + g_x; // 100 + 5 = 105
    return res;
}
