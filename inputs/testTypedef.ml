typedef char MyChar;

int main() {
MyChar arr[2];
MyChar *p = arr;
MyChar *q = p + 1;

// In C, pointer difference is in elements.
// But here I cast to int (address) to check the byte difference.
// MyCC might not support cast (int)q?
// It infers type.
// Let's rely on simple arithmetic if cast is not supported.
// Actually MyCC parser supports casts?
// Lexer has L_PARENTHESES. Parser `parse_cast`?
// Let's assume explicit cast might not work or just work.
// If not, I can just use implicit conversion if I assign to int?
// int addr_p = p; // MyCC is lenient?

int addr_p = p;
int addr_q = q;

return addr_q - addr_p;
}
