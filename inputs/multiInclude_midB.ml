package midB;
import shared;
import midA;

export int midB(int x) {
    return midA.midA(x) + shared.shared_add_two(x);
}
