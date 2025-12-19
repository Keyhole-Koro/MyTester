import os
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor

INPUT_DIR = "../MyTester/inputs"
OUTPUT_DIR = "../MyTester/outputs"

ASM_PATH = "../MyAssembler/build/myas"
EMU_PATH = "../MyEmulator/build/myemu"

# Test cases: (asm file basename, register to check, expected value)
testcases = [
    #("simpleFunc", "R1", 15),
    #("simpleCondition", "R1", 328),
    #("simpleFor", "R1", 5),
    #("simplePointer", "R1", 12),
    #("simpleBinop", "R1", 3),
    #("simpleWhile", "R1", 15),
    #("complexWhile", "R1", 16),
    ("simpleChar", "R1", 72),
    #("simpleStruct", "R1", 10),
]

results = {}

def colored(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

GREEN = "32"
RED = "31"
YELLOW = "33"
CYAN = "36"

def run_step(command, description, base):
    """Run a subprocess step and return stdout. Record an error on failure."""
    try:
        print(colored(f"[RUNNING] {description}:", CYAN), ' '.join(command))
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(colored(f"[OK] {description}", GREEN))
        if result.stdout.strip():
            print(result.stdout)
        if result.stderr.strip():
            print(result.stderr)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(colored(f"[ERROR] {description} failed!", RED))
        print(f"  Command: {' '.join(command)}")
        print(f"  Return code: {e.returncode}")
        print(f"  Output:\n{e.stdout}")
        print(f"  Error:\n{e.stderr}")
        results.setdefault(base, []).append(f"❌ {description}")
        return None

def clean_all():
    """Run make clean for all components"""
    print("[INFO] Cleaning all components...\n")
    run_step(["make", "-C", "../MyAssembler", "clean"], "Clean MyAssembler", "CLEAN")
    run_step(["make", "-C", "../MyEmulator", "clean"], "Clean MyEmulator", "CLEAN")

def build_all():
    """Build all components in parallel"""
    print("[INFO] Building all components...\n")
    build_commands = [
        (["make", "-C", "../MyAssembler", "clean", "all"], "Build MyAssembler"),
        (["make", "-C", "../MyEmulator", "clean", "all"], "Build MyEmulator"),
    ]
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(run_step, cmd, desc, "BUILD")
            for cmd, desc in build_commands
        ]
        for f in futures:
            f.result()

def run_test(basename, reg, expected):
    """Run the test pipeline: ASM -> BIN -> Emulator"""
    asm_path = os.path.join(INPUT_DIR, basename + ".masm")
    bin_path = os.path.join(OUTPUT_DIR, basename + ".bin")

    asm_rel = os.path.relpath(asm_path)
    bin_rel = os.path.relpath(bin_path)

    results[basename] = []

    # Step 1: Assemble ASM -> BIN
    if run_step([ASM_PATH, asm_rel, bin_rel], f"ASM to BIN: {basename}.masm", basename) is None:
        return

    # Step 2: Run Emulator
    output = run_step([EMU_PATH, "-i", bin_rel, "--reg", reg], f"Run Emulator: {basename}.bin", basename)
    if output is None:
        results[basename].append("❌ Emulator execution failed")
        return

    # Extract the last line and check if it matches the expected value
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        results[basename].append("❌ No output from emulator")
        return
    try:
        actual = int(lines[-1])
        if actual == expected:
            results[basename].append(f"✅ {reg} = {actual} (expected)")
        else:
            results[basename].append(f"❌ {reg} = {actual}, expected {expected}")
    except Exception as e:
        results[basename].append(f"❌ Failed to parse reg value: '{lines[-1]}' ({e})")

def run_tests(selected=None):
    """Run all tests or a specific one if selected"""
    print("\n[INFO] Running tests...\n")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if selected:
        matches = [t for t in testcases if t[0] == selected]
        if not matches:
            print(f"[ERROR] Test case '{selected}' not found.")
            sys.exit(1)
        to_run = matches
    else:
        to_run = testcases

    with ThreadPoolExecutor() as executor:
        executor.map(lambda t: run_test(*t), to_run)

    print("\n====== TEST SUMMARY ======")
    for name in sorted(results.keys()):
        print(f"[{name}]")
        for r in results[name]:
            print(f"  {r}")
    print("==========================")

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
        base, ext = os.path.splitext(filename)
        basename = base if ext else filename
    else:
        basename = None

    clean_all()
    build_all()
    run_tests(basename)
