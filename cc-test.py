import os
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor

INPUT_DIR = "../MyTester/inputs"
OUTPUT_DIR = "../MyTester/outputs"

CC_PATH = "../MyCC/mycc"
ASM_PATH = "../MyAssembler/build/myas"
EMU_PATH = "../MyEmulator/build/myemu"

# Test cases: (basename, register to check, expected value)
testcases = [
    ("simpleFunc", "R1", 15),
    ("simpleCondition", "R1", 328),
    ("simpleFor", "R1", 5),
    ("simplePointer", "R1", 5),
    ("simpleBinop", "R1", 3),
]

results = {}

def run_step(command, description, base):
    """Run a subprocess and handle output/errors"""
    try:
        print(f"[RUNNING] {description}: {' '.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"[OK] {description}")
        if result.stdout.strip():
            print(result.stdout)
        if result.stderr.strip():
            print(result.stderr)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed!")
        print(f"  Command: {' '.join(command)}")
        print(f"  Return code: {e.returncode}")
        print(f"  Output:\n{e.stdout}")
        print(f"  Error:\n{e.stderr}")
        results.setdefault(base, []).append(f"❌ {description}")
        return None

def build_all():
    """Build all subprojects before running tests"""
    print("[INFO] Building all components...\n")
    run_step(["make", "-C", "../MyCC"], "Build MyCC", "BUILD")
    run_step(["make", "-C", "../MyAssembler"], "Build MyAssembler", "BUILD")
    run_step(["make", "-C", "../MyEmulator"], "Build MyEmulator", "BUILD")

def run_test(basename, reg, expected):
    """Run the full pipeline for a single test case"""
    c_path = os.path.join(INPUT_DIR, basename + ".c")
    asm_path = os.path.join(OUTPUT_DIR, basename + ".masm")
    bin_path = os.path.join(OUTPUT_DIR, basename + ".bin")

    c_path_rel = os.path.relpath(c_path)
    asm_path_rel = os.path.relpath(asm_path)
    bin_path_rel = os.path.relpath(bin_path)

    ok = True

    if run_step([CC_PATH, c_path_rel, asm_path_rel], f"C to ASM: {basename}.c", basename) is None:
        ok = False
    if run_step([ASM_PATH, asm_path_rel, bin_path_rel], f"ASM to BIN: {basename}.masm", basename) is None:
        ok = False

    if ok:
        output = run_step([EMU_PATH, "-i", bin_path_rel, "--reg", reg], f"Run: {basename}.bin", basename)
        if output is None:
            ok = False
        else:
            try:
                actual = int(output.splitlines()[-1])
                if actual == expected:
                    results.setdefault(basename, []).append(f"✅ {reg} = {actual} (expected)")
                else:
                    results.setdefault(basename, []).append(f"❌ {reg} = {actual}, expected {expected}")
            except Exception as e:
                results.setdefault(basename, []).append(f"❌ Failed to parse reg value: {e}")
                ok = False

    if ok and basename not in results:
        results.setdefault(basename, []).append("✅ All stages passed")

def run_tests(selected=None):
    """Run selected test cases in parallel (or all if not specified)"""
    print("\n[INFO] Running tests...\n")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if selected:
        matches = [t for t in testcases if t[0] == selected]
        if not matches:
            print(f"[ERROR] Test case '{selected}' not found in testcases.")
            sys.exit(1)
        to_run = matches
    else:
        to_run = testcases

    with ThreadPoolExecutor() as executor:
        executor.map(lambda t: run_test(*t), to_run)

    print("\n====== TEST SUMMARY ======")
    for name in sorted(results.keys()):
        print(f"[{name}]")
        for outcome in results[name]:
            print(f"  {outcome}")
    print("==========================")

if __name__ == "__main__":
    # If an argument is given, filter to that test
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
        base, ext = os.path.splitext(filename)
        basename = base if ext else filename
    else:
        basename = None

    build_all()
    run_tests(basename)
