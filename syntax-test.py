import os
import subprocess
import sys

CC_PATH = "../MyCC/mycc"
ASM_PATH = "../MyAssembler/build/myas"

INPUT_DIR = "../MyTester/inputs"
OUTPUT_DIR = "../MyTester/outputs"


def colored(text, code):
    return f"\033[{code}m{text}\033[0m"


GREEN = "32"
RED = "31"
CYAN = "36"


def run_step(cmd, desc, expect_fail=False, expect_substr=None):
    print(colored(f"[RUNNING] {desc}:", CYAN), " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if expect_fail:
        if result.returncode == 0:
            print(colored(f"[ERROR] {desc} unexpectedly succeeded", RED))
            if result.stdout.strip():
                print(result.stdout)
            if result.stderr.strip():
                print(result.stderr)
            return False
        if expect_substr and expect_substr not in (result.stderr or ""):
            print(colored(f"[ERROR] {desc} did not emit expected text '{expect_substr}'", RED))
            if result.stdout.strip():
                print(result.stdout)
            if result.stderr.strip():
                print(result.stderr)
            return False
        print(colored(f"[OK] {desc} failed as expected", GREEN))
        if result.stderr.strip():
            print(result.stderr)
        return True
    else:
        if result.returncode != 0:
            print(colored(f"[ERROR] {desc} failed (rc={result.returncode})", RED))
            if result.stdout.strip():
                print(result.stdout)
            if result.stderr.strip():
                print(result.stderr)
            return False
        print(colored(f"[OK] {desc}", GREEN))
        if result.stdout.strip():
            print(result.stdout)
        return True


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Build CC + Assembler
    steps = [
        (["make", "-C", "../MyCC", "clean", "all"], "Build MyCC", False, None),
        (["make", "-C", "../MyAssembler", "clean", "all"], "Build MyAssembler", False, None),
    ]
    ok = True
    for cmd, desc, exp_fail, substr in steps:
        if not run_step(cmd, desc, exp_fail, substr):
            ok = False
    if not ok:
        sys.exit(1)

    tests = [
        (
            [CC_PATH, os.path.join(INPUT_DIR, "invalidSyntax.c"), os.path.join(OUTPUT_DIR, "invalidSyntax.masm")],
            "MyCC syntax error",
            True,
            "error:",
        ),
        (
            [ASM_PATH, os.path.join(INPUT_DIR, "invalidAsm.masm"), os.path.join(OUTPUT_DIR, "invalidAsm.bin")],
            "MyAssembler syntax error",
            True,
            "error:",
        ),
    ]

    all_passed = True
    for cmd, desc, exp_fail, substr in tests:
        if not run_step(cmd, desc, exp_fail, substr):
            all_passed = False

    if all_passed:
        print(colored("\nAll syntax error tests passed.", GREEN))
    else:
        print(colored("\nSyntax error tests FAILED.", RED))
        sys.exit(1)


if __name__ == "__main__":
    main()
