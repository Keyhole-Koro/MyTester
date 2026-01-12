import os
import sys
import shutil
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT_DIR = Path("/workspaces/MyComputer")
INPUT_DIR = ROOT_DIR / "MyTester/inputs"
OUTPUT_DIR = ROOT_DIR / "MyTester/outputs"

CC_PATH = ROOT_DIR / "MyLangCompiler/mlc"
ASM_PATH = ROOT_DIR / "MyAssembler/build/myas"
LINKER_PATH = ROOT_DIR / "MyLangLinker/mllinker"
EMU_PATH = ROOT_DIR / "MyEmulator/build/myemu"
EMU_TIMEOUT_SEC = float(os.environ.get("EMU_TIMEOUT_SEC", "8"))

# Test cases: (basename, sources list, register to check, expected value)
testcases = [
    ("simpleFunc", ["simpleFunc.ml"], "R1", 15),
    ("simpleCondition", ["simpleCondition.ml"], "R1", 328),
    ("simpleFor", ["simpleFor.ml"], "R1", 5),
    ("simplePointer", ["simplePointer.ml"], "R1", 14),
    ("simpleBinop", ["simpleBinop.ml"], "R1", 3),
    ("simpleWhile", ["simpleWhile.ml"], "R1", 15),
    ("complexWhile", ["complexWhile.ml"], "R1", 16),
    ("simpleChar", ["simpleChar.ml"], "R1", 72),
    ("simpleStruct", ["simpleStruct.ml"], "R1", 10),
    ("arrayInit", ["arrayInit.ml"], "R1", 106),
    ("multiArray", ["multiArray.ml"], "R1", 6),
    ("arraySizeof", ["arraySizeof.ml"], "R1", 24),
    ("testDoWhile", ["testDoWhile.ml"], "R1", 10),
    ("testBitwise", ["testBitwise.ml"], "R1", 29),
    ("testOps", ["testOps.ml"], "R1", 10),
    ("testTernary", ["testTernary.ml"], "R1", 8),
    ("testTypedef", ["testTypedef.ml"], "R1", 1),
    ("longProgram", ["longProgram.ml"], "R1", 77),
    ("complex_ops", ["complex_ops.ml"], "R1", 188),
    ("multiInclude", ["multiInclude.ml", "multiInclude_part1.ml", "multiInclude_part2.ml"], "R1", 11),
    ("multiInclude_complex", ["multiInclude_complex.ml", "multiInclude_midA.ml", "multiInclude_midB.ml", "multiInclude_shared.ml"], "R1", 21),
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

def has_failure(outcomes):
    """Return True if any outcome marks a failure."""
    return any(msg.startswith("❌") for msg in outcomes)

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
    run_step(["make", "-C", str(ROOT_DIR / "MyLangCompiler"), "clean"], "Clean MyLangCompiler", "CLEAN")
    run_step(["make", "-C", str(ROOT_DIR / "MyAssembler"), "clean"], "Clean MyAssembler", "CLEAN")
    run_step(["make", "-C", str(ROOT_DIR / "MyLangLinker"), "clean"], "Clean MyLangLinker", "CLEAN")
    run_step(["make", "-C", str(ROOT_DIR / "MyEmulator"), "clean"], "Clean MyEmulator", "CLEAN")

def build_all():
    """Build all components in parallel"""
    print("[INFO] Building all components...\n")

    build_commands = [
        (["make", "-C", str(ROOT_DIR / "MyLangCompiler"), "clean", "all"], "Build MyLangCompiler"),
        (["make", "-C", str(ROOT_DIR / "MyAssembler"), "clean", "all"], "Build MyAssembler"),
        (["make", "-C", str(ROOT_DIR / "MyLangLinker"), "clean", "all"], "Build MyLangLinker"),
        (["make", "-C", str(ROOT_DIR / "MyEmulator"), "clean", "all"], "Build MyEmulator"),
    ]

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(run_step, cmd, desc, "BUILD")
            for cmd, desc in build_commands
        ]
        for future in futures:
            future.result()


def run_test(basename, sources, reg, expected):
    """Run the full pipeline for a single test case: per-source CC/AS -> Linker -> Emulator"""
    obj_paths = []
    bin_path = OUTPUT_DIR / f"{basename}.bin"

    results[basename] = []

    for src in sources:
        src_path = INPUT_DIR / src
        stem = src_path.stem
        asm_path = OUTPUT_DIR / f"{basename}__{stem}.masm"
        bin_prelink_path = OUTPUT_DIR / f"{basename}__{stem}.prelink.bin"
        obj_path = OUTPUT_DIR / f"{basename}__{stem}.obj"

        if run_step([str(CC_PATH), str(src_path), str(asm_path)], f"C to ASM: {src}", basename) is None:
            return

        if run_step([str(ASM_PATH), str(asm_path), str(bin_prelink_path), "--obj", str(obj_path)], f"ASM to OBJ: {src}", basename) is None:
            return

        obj_paths.append(str(obj_path))

    if run_step([str(LINKER_PATH), str(bin_path)] + obj_paths, f"Link OBJ to BIN: {basename}", basename) is None:
        return

    # Run Emulator and capture output
    emu_cmd = [str(EMU_PATH), "-i", str(bin_path), "--reg", reg]
    print(colored(f"[INFO] Next: emulator command for {basename}", YELLOW), " ".join(emu_cmd))
    output = run_step(emu_cmd, f"Run Emulator: {basename}.bin", basename, timeout=EMU_TIMEOUT_SEC)

    if os.path.exists("memory_dump.txt"):
        shutil.move("memory_dump.txt", os.path.join(OUTPUT_DIR, "memory_dump.txt"))

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
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if selected:
        matches = [t for t in testcases if t[0] == selected]
        if not matches:
            print(f"[ERROR] Test case '{selected}' not found in testcases.")
            sys.exit(1)
        to_run = matches
    else:
        to_run = testcases

    # Run sequentially to avoid stdout buffering/timeouts when many emulators run.
    for t in to_run:
        run_test(*t)

    print("\n====== TEST SUMMARY ======")
    failures = []
    successes = []

    for name in sorted(results.keys()):
        bucket = failures if has_failure(results[name]) else successes
        bucket.append((name, results[name]))

    for name, outcomes in successes:
        print(f"[{name}]")
        for outcome in outcomes:
            print(f"  {outcome}")

    if failures:
        if successes:
            print()
        print("-- Failures (bottom) --")
        for name, outcomes in failures:
            print(f"[{name}]")
            for outcome in outcomes:
                print(f"  {outcome}")
        print(f"Failed cases: {', '.join(name for name, _ in failures)}")
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
