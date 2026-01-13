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
LINKER_PATH = ROOT_DIR / "MyLinker/mllinker"
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
    ("testStmtExpr", ["testStmtExpr.ml"], "R1", 5),
    ("testCaseExpr", ["testCaseExpr.ml"], "R1", 30),
    ("testCaseStructArrow", ["testCaseStructArrow.ml"], "R1", 42),
    ("testCaseComplex", ["testCaseComplex.ml"], "R1", 400),
    ("testCaseExprRef", ["testCaseExprRef.ml"], "R1", 100),
    ("nestedCaseArrow", ["nestedCaseArrow.ml"], "R1", 10),
    ("packageSample", ["pkg_main.ml", "pkg_math.ml"], "R1", 20),
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

def case_dir(base):
    """Return (and create) the output subdir for this base/test name."""
    path = OUTPUT_DIR / base
    path.mkdir(parents=True, exist_ok=True)
    return path

def run_step(command, description, base, timeout=None, out_dir=None):
    """Run a subprocess and handle output/errors"""
    log_root = out_dir if out_dir else OUTPUT_DIR
    log_root.mkdir(parents=True, exist_ok=True)
    log_file_path = log_root / f"{base}.log"
    try:
        pretty = ' '.join(command)
        print(colored(f"[RUNNING] {description}", CYAN)) # Minimal output to terminal
        
        # Append to log file
        with open(log_file_path, "a") as log_file:
            log_file.write(f"\n--- {description} ---\nCommand: {pretty}\n")
            
            result = subprocess.run(
                command, check=True, capture_output=True, text=True, timeout=timeout
            )
            
            log_file.write(f"STDOUT:\n{result.stdout}\n")
            log_file.write(f"STDERR:\n{result.stderr}\n")

        print(colored(f"[OK] {description}", GREEN))
        return result.stdout.strip()

    except subprocess.TimeoutExpired as e:
        print(colored(f"[ERROR] {description} timed out after {timeout}s!", RED))
        # Log failure details
        with open(log_file_path, "a") as log_file:
             log_file.write(f"\n[TIMEOUT] {description}\n")
             log_file.write(f"Partial STDOUT:\n{e.stdout}\n")
             log_file.write(f"Partial STDERR:\n{e.stderr}\n")

        print(f"  See {log_file_path} for details.")
        results.setdefault(base, []).append(f"❌ {description} timed out ({timeout}s)")
        return None

    except subprocess.CalledProcessError as e:
        print(colored(f"[ERROR] {description} failed!", RED))
        
        with open(log_file_path, "a") as log_file:
             log_file.write(f"\n[FAILED] {description}\n")
             log_file.write(f"Return Code: {e.returncode}\n")
             log_file.write(f"STDOUT:\n{e.stdout}\n")
             log_file.write(f"STDERR:\n{e.stderr}\n")
             
        print(f"  See {log_file_path} for details.")
        results.setdefault(base, []).append(f"❌ {description}")
        return None
    except Exception as e:
         print(colored(f"[ERROR] {description} unexpected error: {e}", RED))
         results.setdefault(base, []).append(f"❌ {description} error: {e}")
         return None

def clean_all():
    """Run make clean for all components"""
    print("[INFO] Cleaning all components...\n")
    clean_dir = case_dir("CLEAN")
    run_step(["make", "-C", str(ROOT_DIR / "MyLangCompiler"), "clean"], "Clean MyLangCompiler", "CLEAN", out_dir=clean_dir)
    run_step(["make", "-C", str(ROOT_DIR / "MyAssembler"), "clean"], "Clean MyAssembler", "CLEAN", out_dir=clean_dir)
    run_step(["make", "-C", str(ROOT_DIR / "MyLinker"), "clean"], "Clean MyLinker", "CLEAN", out_dir=clean_dir)
    run_step(["make", "-C", str(ROOT_DIR / "MyEmulator"), "clean"], "Clean MyEmulator", "CLEAN", out_dir=clean_dir)

def build_all():
    """Build all components in parallel"""
    print("[INFO] Building all components...\n")

    build_commands = [
        (["make", "-C", str(ROOT_DIR / "MyLangCompiler"), "all"], "Build MyLangCompiler"),
        (["make", "-C", str(ROOT_DIR / "MyAssembler"), "all"], "Build MyAssembler"),
        (["make", "-C", str(ROOT_DIR / "MyLinker"), "all"], "Build MyLinker"),
        (["make", "-C", str(ROOT_DIR / "MyEmulator"), "all"], "Build MyEmulator"),
    ]

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(run_step, cmd, desc, "BUILD", out_dir=case_dir("BUILD")): desc
            for cmd, desc in build_commands
        }
        for future in futures:
            if future.result() is None:
                print(f"[FATAL] {futures[future]} failed. Exiting.")
                sys.exit(1)


def run_test(basename, sources, reg, expected):
    """Run the full pipeline for a single test case: per-source CC/AS -> Linker -> Emulator"""
    test_dir = case_dir(basename)
    obj_paths = []
    bin_path = test_dir / f"{basename}.bin"

    results[basename] = []

    for src in sources:
        src_path = INPUT_DIR / src
        stem = src_path.stem
        asm_path = test_dir / f"{basename}__{stem}.masm"
        bin_prelink_path = test_dir / f"{basename}__{stem}.prelink.bin"
        obj_path = test_dir / f"{basename}__{stem}.obj"

        if run_step([str(CC_PATH), str(src_path), str(asm_path)], f"C to ASM: {src}", basename, out_dir=test_dir) is None:
            return

        if run_step([str(ASM_PATH), str(asm_path), str(bin_prelink_path), "--obj", str(obj_path)], f"ASM to OBJ: {src}", basename, out_dir=test_dir) is None:
            return

        obj_paths.append(str(obj_path))

    if run_step([str(LINKER_PATH), str(bin_path)] + obj_paths, f"Link OBJ to BIN: {basename}", basename, out_dir=test_dir) is None:
        return

    # Run Emulator and capture output
    emu_cmd = [str(EMU_PATH), "-i", str(bin_path), "--reg", reg]
    print(colored(f"[INFO] Next: emulator command for {basename}", YELLOW), " ".join(emu_cmd))
    output = run_step(emu_cmd, f"Run Emulator: {basename}.bin", basename, timeout=EMU_TIMEOUT_SEC, out_dir=test_dir)

    if os.path.exists("memory_dump.txt"):
        shutil.move("memory_dump.txt", os.path.join(test_dir, "memory_dump.txt"))

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

    # clean_all() # Disabled to allow incremental builds
    build_all()
    run_tests(basename)
