import os
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor

INPUT_DIR = "../MyTester/inputs"
OUTPUT_DIR = "../MyTester/outputs"

CC_PATH = "../MyCC/mycc"
ASM_PATH = "../MyAssembler/build/myas"
EMU_PATH = "../MyEmulator/build/myemu"
EMU_TIMEOUT_SEC = float(os.environ.get("EMU_TIMEOUT_SEC", "8"))

# Test cases: (basename, register to check, expected value)
testcases = [
    ("simpleFunc", "R1", 15),
    ("simpleCondition", "R1", 328),
    ("simpleFor", "R1", 5),
    ("simplePointer", "R1", 14),
    ("simpleBinop", "R1", 3),
    ("simpleWhile", "R1", 15),
    ("complexWhile", "R1", 16),
    ("simpleChar", "R1", 72),
    ("simpleStruct", "R1", 10),
    ("arrayInit", "R1", 106),
]

results = {}

def colored(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

GREEN = "32"     # Success
RED = "31"       # Error
YELLOW = "33"    # Warning
CYAN = "36"
BOLD = "1"

def fmt_hex(v: int) -> str:
    """Format integer as 0x-prefixed lowercase hex (no leading zeros)."""
    return f"0x{v:x}"

def run_step(command, description, base, timeout=None):
    """Run a subprocess and handle output/errors"""
    try:
        pretty = ' '.join(command)
        print(colored(f"[RUNNING] {description}:", CYAN), pretty)
        result = subprocess.run(
            command, check=True, capture_output=True, text=True, timeout=timeout
        )
        print(colored(f"[OK] {description}", GREEN))
        if result.stdout.strip():
            print(result.stdout)
        if result.stderr.strip():
            print(result.stderr)
        return result.stdout.strip()
    except subprocess.TimeoutExpired as e:
        print(colored(f"[ERROR] {description} timed out after {timeout}s!", RED))
        print(f"  Command: {' '.join(command)}")
        print(f"  Partial output:\n{(e.stdout or '').strip()}")
        print(f"  Partial error:\n{(e.stderr or '').strip()}")
        results.setdefault(base, []).append(f"❌ {description} timed out ({timeout}s)")
        return None
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
    run_step(["make", "-C", "../MyCC", "clean"], "Clean MyCC", "CLEAN")
    run_step(["make", "-C", "../MyAssembler", "clean"], "Clean MyAssembler", "CLEAN")
    run_step(["make", "-C", "../MyEmulator", "clean"], "Clean MyEmulator", "CLEAN")

def build_all():
    """Build all components in parallel"""
    print("[INFO] Building all components...\n")

    build_commands = [
        (["make", "-C", "../MyCC", "clean", "all"], "Build MyCC"),
        (["make", "-C", "../MyAssembler", "clean", "all"], "Build MyAssembler"),
        (["make", "-C", "../MyEmulator", "clean", "all"], "Build MyEmulator"),
    ]

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(run_step, cmd, desc, "BUILD")
            for cmd, desc in build_commands
        ]
        for future in futures:
            future.result()


def run_test(basename, reg, expected):
    """Run the full pipeline for a single test case"""
    c_path = os.path.join(INPUT_DIR, basename + ".c")
    asm_path = os.path.join(OUTPUT_DIR, basename + ".masm")
    bin_path = os.path.join(OUTPUT_DIR, basename + ".bin")

    c_path_rel = os.path.relpath(c_path)
    asm_path_rel = os.path.relpath(asm_path)
    bin_path_rel = os.path.relpath(bin_path)

    results[basename] = []

    # Step 1: Compile C to ASM
    if run_step([CC_PATH, c_path_rel, asm_path_rel], f"C to ASM: {basename}.c", basename) is None:
        return

    # Step 2: Assemble ASM to BIN
    if run_step([ASM_PATH, asm_path_rel, bin_path_rel], f"ASM to BIN: {basename}.masm", basename) is None:
        return

    # Step 3: Run Emulator and capture output
    emu_cmd = [EMU_PATH, "-i", bin_path_rel, "--reg", reg]
    print(colored(f"[INFO] Next: emulator command for {basename}", YELLOW), " ".join(emu_cmd))
    output = run_step(emu_cmd, f"Run Emulator: {basename}.bin", basename, timeout=EMU_TIMEOUT_SEC)
    if output is None:
        results[basename].append("❌ Emulator execution failed")
        return

    # Step 4: Parse register value
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        results[basename].append("❌ No output from emulator")
        return

    try:
        # Accept decimal or hex (e.g., "0x1f")
        actual = int(lines[-1], 0)
        if actual == expected:
            results[basename].append(f"✅ {reg} = {fmt_hex(actual)} (expected)")
        else:
            results[basename].append(f"❌ {reg} = {fmt_hex(actual)}, expected {fmt_hex(expected)}")
    except Exception as e:
        results[basename].append(f"❌ Failed to parse reg value: '{lines[-1]}' ({e})")


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

    clean_all()
    build_all()
    run_tests(basename)
