import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.project_paths import (
    MYASSEMBLER_DIR,
    MYEMULATOR_DIR,
    MYLANGCOMPILER_DIR,
    MYLINKER_DIR,
    MYTESTER_DIR,
    REPO_ROOT,
)

ROOT_DIR = REPO_ROOT
INPUT_DIR = MYTESTER_DIR / "inputs"
OUTPUT_DIR = MYTESTER_DIR / "outputs"

CC_PATH = MYLANGCOMPILER_DIR / "mlc"
ASM_PATH = MYASSEMBLER_DIR / "build/myas"
LINKER_PATH = MYLINKER_DIR / "mllinker"
EMU_PATH = MYEMULATOR_DIR / "build/myemu"
EMU_TIMEOUT_SEC = float(os.environ.get("EMU_TIMEOUT_SEC", "8"))

# Test cases: (basename, sources list, register to check, expected value)
testcases = [
    ("simpleFunc", ["simpleFunc.mln"], "R1", 15),
    ("simpleCondition", ["simpleCondition.mln"], "R1", 328),
    ("simpleFor", ["simpleFor.mln"], "R1", 5),
    ("simplePointer", ["simplePointer.mln"], "R1", 14),
    ("simpleBinop", ["simpleBinop.mln"], "R1", 3),
    ("simpleWhile", ["simpleWhile.mln"], "R1", 15),
    ("complexWhile", ["complexWhile.mln"], "R1", 16),
    ("simpleChar", ["simpleChar.mln"], "R1", 72),
    ("intWidth32", ["intWidth32.mln"], "R1", 20),
    ("simpleStruct", ["simpleStruct.mln"], "R1", 10),
    ("arrayInit", ["arrayInit.mln"], "R1", 106),
    ("multiArray", ["multiArray.mln"], "R1", 6),
    ("arraySizeof", ["arraySizeof.mln"], "R1", 24),
    ("testDoWhile", ["testDoWhile.mln"], "R1", 10),
    ("testBitwise", ["testBitwise.mln"], "R1", 29),
    ("testOps", ["testOps.mln"], "R1", 10),
    ("testTernary", ["testTernary.mln"], "R1", 8),
    ("testTypedef", ["testTypedef.mln"], "R1", 1),
    ("longProgram", ["longProgram.mln"], "R1", 77),
    ("complex_ops", ["complex_ops.mln"], "R1", 188),
    ("multiInclude", ["multiInclude.mln", "multiInclude_part1.mln", "multiInclude_part2.mln"], "R1", 11),
    ("multiInclude_complex", ["multiInclude_complex.mln", "multiInclude_midA.mln", "multiInclude_midB.mln", "multiInclude_shared.mln"], "R1", 21),
    ("testStmtExpr", ["testStmtExpr.mln"], "R1", 5),
    ("testCaseExpr", ["testCaseExpr.mln"], "R1", 30),
    ("testCaseStructArrow", ["testCaseStructArrow.mln"], "R1", 42),
    ("testCaseComplex", ["testCaseComplex.mln"], "R1", 400),
    ("testCaseExprRef", ["testCaseExprRef.mln"], "R1", 100),
    ("nestedCaseArrow", ["nestedCaseArrow.mln"], "R1", 10),
    ("packageSample", ["pkg_main.mln", "pkg_math.mln"], "R1", 20),
    ("functionLiteral", ["functionLiteral.mln"], "R1", 10),
    ("localFunctionLiteral", ["localFunctionLiteral.mln"], "R1", 10),
    ("nestedFunctionLiteral", ["nestedFunctionLiteral.mln"], "R1", 6),
    ("globalInit", ["globalInit.mln"], "R1", 42),
    ("testGlobalScalar", ["testGlobalScalar.mln"], "R1", 105),
    ("globalUninit", ["globalUninit.mln"], "R1", 83),
]

results = {}
VERBOSE = False

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

def status_line(label, message, color=CYAN):
    print(colored(f"[{label}]", color), message)

def case_dir(base):
    """Return (and create) the output subdir for this base/test name."""
    path = OUTPUT_DIR / base
    path.mkdir(parents=True, exist_ok=True)
    return path

def run_step(command, description, base, timeout=None, out_dir=None, outcomes=None, cwd=None):
    """Run a subprocess and handle output/errors"""
    log_root = out_dir if out_dir else OUTPUT_DIR
    log_root.mkdir(parents=True, exist_ok=True)
    log_file_path = log_root / f"{base}.log"
    if outcomes is None:
        outcomes = results.setdefault(base, [])
    try:
        pretty = ' '.join(command)
        if VERBOSE:
            status_line("RUN", description, CYAN)
        
        # Append to log file
        with open(log_file_path, "a") as log_file:
            log_file.write(f"\n--- {description} ---\nCommand: {pretty}\n")
            
            result = subprocess.run(
                command, check=True, capture_output=True, text=True, timeout=timeout, cwd=cwd
            )
            
            log_file.write(f"STDOUT:\n{result.stdout}\n")
            log_file.write(f"STDERR:\n{result.stderr}\n")

        if VERBOSE:
            status_line("OK", description, GREEN)
        return result.stdout.strip()

    except subprocess.TimeoutExpired as e:
        # Log failure details
        with open(log_file_path, "a") as log_file:
             log_file.write(f"\n[TIMEOUT] {description}\n")
             log_file.write(f"Partial STDOUT:\n{e.stdout}\n")
             log_file.write(f"Partial STDERR:\n{e.stderr}\n")

        outcomes.append(f"❌ {description} timed out ({timeout}s)")
        outcomes.append(f"   log: {log_file_path}")
        return None

    except subprocess.CalledProcessError as e:
        with open(log_file_path, "a") as log_file:
             log_file.write(f"\n[FAILED] {description}\n")
             log_file.write(f"Return Code: {e.returncode}\n")
             log_file.write(f"STDOUT:\n{e.stdout}\n")
             log_file.write(f"STDERR:\n{e.stderr}\n")

        outcomes.append(f"❌ {description}")
        outcomes.append(f"   log: {log_file_path}")
        return None
    except Exception as e:
         outcomes.append(f"❌ {description} error: {e}")
         return None

def clean_all():
    """Run make clean for all components"""
    status_line("SETUP", "clean toolchain")
    clean_dir = case_dir("CLEAN")
    run_step(["make", "-C", str(MYLANGCOMPILER_DIR), "clean"], "Clean MyLangCompiler", "CLEAN", out_dir=clean_dir)
    run_step(["make", "-C", str(MYASSEMBLER_DIR), "clean"], "Clean MyAssembler", "CLEAN", out_dir=clean_dir)
    run_step(["make", "-C", str(MYLINKER_DIR), "clean"], "Clean MyLinker", "CLEAN", out_dir=clean_dir)
    run_step(["make", "-C", str(MYEMULATOR_DIR), "clean"], "Clean MyEmulator", "CLEAN", out_dir=clean_dir)

def build_all():
    """Build all components in parallel"""
    status_line("SETUP", "build toolchain")

    build_commands = [
        (["make", "-C", str(MYLANGCOMPILER_DIR), "all"], "Build MyLangCompiler"),
        (["make", "-C", str(MYASSEMBLER_DIR), "all"], "Build MyAssembler"),
        (["make", "-C", str(MYLINKER_DIR), "all"], "Build MyLinker"),
        (["make", "-C", str(MYEMULATOR_DIR), "all"], "Build MyEmulator"),
    ]

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(run_step, cmd, desc, "BUILD", out_dir=case_dir("BUILD")): desc
            for cmd, desc in build_commands
        }
        for future in futures:
            if future.result() is None:
                status_line("FATAL", f"{futures[future]} failed", RED)
                sys.exit(1)


def run_test(basename, sources, reg, expected):
    """Run the full pipeline for a single test case: per-source CC/AS -> Linker -> Emulator"""
    test_dir = case_dir(basename)
    obj_paths = []
    bin_path = test_dir / f"{basename}.mbin"
    outcomes = []

    for src in sources:
        src_path = INPUT_DIR / src
        stem = src_path.stem
        asm_path = test_dir / f"{basename}__{stem}.masm"
        bin_prelink_path = test_dir / f"{basename}__{stem}.prelink.mbin"
        obj_path = test_dir / f"{basename}__{stem}.mobj"

        if run_step([str(CC_PATH), str(src_path), str(asm_path)], f"C to ASM: {src}", basename, out_dir=test_dir, outcomes=outcomes, cwd=test_dir) is None:
            return basename, outcomes

        if run_step([str(ASM_PATH), str(asm_path), str(bin_prelink_path), "--obj", str(obj_path)], f"ASM to OBJ: {src}", basename, out_dir=test_dir, outcomes=outcomes, cwd=test_dir) is None:
            return basename, outcomes

        obj_paths.append(str(obj_path))

    if run_step([str(LINKER_PATH), str(bin_path)] + obj_paths, f"Link MOBJ to MBIN: {basename}", basename, out_dir=test_dir, outcomes=outcomes, cwd=test_dir) is None:
        return basename, outcomes

    # Run Emulator and capture output
    emu_cmd = [str(EMU_PATH), "-i", str(bin_path), "--reg", reg]
    if VERBOSE:
        status_line("EMU", " ".join(emu_cmd), YELLOW)
    output = run_step(emu_cmd, f"Run Emulator: {basename}.mbin", basename, timeout=EMU_TIMEOUT_SEC, out_dir=test_dir, outcomes=outcomes, cwd=test_dir)

    if output is None:
        outcomes.append("❌ Emulator execution failed")
        return basename, outcomes

    # Step 4: Parse register value
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        outcomes.append("❌ No output from emulator")
        return basename, outcomes

    try:
        # Accept decimal or hex (e.g., "0x1f")
        actual = int(lines[-1], 0)
        if actual == expected:
            outcomes.append(f"✅ {reg} = {fmt_hex(actual)} (expected)")
        else:
            outcomes.append(f"❌ {reg} = {fmt_hex(actual)}, expected {fmt_hex(expected)}")
    except Exception as e:
        outcomes.append(f"❌ Failed to parse reg value: '{lines[-1]}' ({e})")
    return basename, outcomes


def run_tests(selected=None):
    """Run selected test cases in parallel (or all if not specified)"""
    global results
    results = {}
    status_line("RUN", f"{1 if selected else len(testcases)} case(s)" if selected else f"{len(testcases)} case(s)")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if selected:
        matches = [t for t in testcases if t[0] == selected]
        if not matches:
            print(f"[ERROR] Test case '{selected}' not found in testcases.")
            sys.exit(1)
        to_run = matches
    else:
        to_run = testcases

    max_workers = min(len(to_run), max(1, os.cpu_count() or 4), 8)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(run_test, *t): t[0] for t in to_run}
        for future in as_completed(future_map):
            name, outcomes = future.result()
            results[name] = outcomes

    passed = 0
    failed = 0
    failures = []

    for name in sorted(results.keys()):
        if has_failure(results[name]):
            failed += 1
            failures.append((name, results[name]))
        else:
            passed += 1
            success_msg = next((outcome for outcome in results[name] if outcome.startswith("✅")), "✅ PASS")
            detail = success_msg.removeprefix("✅ ").strip()
            status_line("PASS", f"{name} {detail}", GREEN)

    if failures:
        for name, outcomes in failures:
            summary = next((outcome for outcome in outcomes if outcome.startswith("❌")), "❌ failed")
            status_line("FAIL", f"{name} {summary.removeprefix('❌ ').strip()}", RED)
            if VERBOSE:
                continue
            for outcome in outcomes:
                if outcome.startswith("✅"):
                    continue
                print(f"  {outcome}")

    summary = f"Summary: {passed} passed, {failed} failed"
    status_line("DONE", summary, GREEN if failed == 0 else YELLOW)
    if failures:
        print("Failed cases:", ", ".join(name for name, _ in failures))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MyLang compiler integration tests.")
    parser.add_argument("test", nargs="?", help="Optional test case name or source filename")
    parser.add_argument("--verbose", action="store_true", help="Show step-by-step command progress")
    args = parser.parse_args()

    VERBOSE = args.verbose

    if args.test:
        base, ext = os.path.splitext(args.test)
        basename = base if ext else args.test
    else:
        basename = None

    # clean_all() # Disabled to allow incremental builds
    build_all()
    run_tests(basename)
