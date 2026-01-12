typedef struct {
int x;
int y;
} Point;

void translate(Point *p, int dx, int dy) {
p->x = p->x + dx;
p->y = p->y + dy;
}

int sum(Point *p) {
return p->x + p->y;
}

int main() {
Point p;
p.x = 1;
p.y = 2;

translate(&p, 3, 4); // p becomes (4,6)
return sum(&p);      // 10
}
