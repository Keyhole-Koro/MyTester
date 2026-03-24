import os
import sys
import subprocess
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.project_paths import MYASSEMBLER_DIR, MYEMULATOR_DIR, MYTESTER_DIR, REPO_ROOT

ROOT_DIR = REPO_ROOT
INPUT_DIR = MYTESTER_DIR / "inputs"
OUTPUT_DIR = MYTESTER_DIR / "outputs"

ASM_PATH = MYASSEMBLER_DIR / "build/myas"
EMU_PATH = MYEMULATOR_DIR / "build/myemu"

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
VERBOSE = False

def colored(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

GREEN = "32"
RED = "31"
YELLOW = "33"
CYAN = "36"

def status_line(label, message, color=CYAN):
    print(colored(f"[{label}]", color), message)

def has_failure(outcomes):
    return any(msg.startswith("❌") for msg in outcomes)

def run_step(command, description, base, log_path=None):
    """Run a subprocess step and return stdout. Record an error on failure."""
    if log_path is None:
        log_path = OUTPUT_DIR / f"{base}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if VERBOSE:
            status_line("RUN", description, CYAN)
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        with open(log_path, "a") as log_file:
            log_file.write(f"\n--- {description} ---\n")
            log_file.write(f"Command: {' '.join(command)}\n")
            log_file.write(f"STDOUT:\n{result.stdout}\n")
            log_file.write(f"STDERR:\n{result.stderr}\n")
        if VERBOSE:
            status_line("OK", description, GREEN)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        with open(log_path, "a") as log_file:
            log_file.write(f"\n[FAILED] {description}\n")
            log_file.write(f"Command: {' '.join(command)}\n")
            log_file.write(f"Return Code: {e.returncode}\n")
            log_file.write(f"STDOUT:\n{e.stdout}\n")
            log_file.write(f"STDERR:\n{e.stderr}\n")
        results.setdefault(base, []).append(f"❌ {description}")
        results.setdefault(base, []).append(f"   log: {log_path}")
        return None

def clean_all():
    """Run make clean for all components"""
    status_line("SETUP", "clean toolchain")
    clean_log = OUTPUT_DIR / "CLEAN.log"
    run_step(["make", "-C", str(MYASSEMBLER_DIR), "clean"], "Clean MyAssembler", "CLEAN", log_path=clean_log)
    run_step(["make", "-C", str(MYEMULATOR_DIR), "clean"], "Clean MyEmulator", "CLEAN", log_path=clean_log)

def build_all():
    """Build all components in parallel"""
    status_line("SETUP", "build assembler and emulator")
    build_log = OUTPUT_DIR / "BUILD.log"
    build_commands = [
        (["make", "-C", str(MYASSEMBLER_DIR), "clean", "all"], "Build MyAssembler"),
        (["make", "-C", str(MYEMULATOR_DIR), "clean", "all"], "Build MyEmulator"),
    ]
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(run_step, cmd, desc, "BUILD", build_log)
            for cmd, desc in build_commands
        ]
        for f in futures:
            if f.result() is None:
                status_line("FATAL", "build failed", RED)
                sys.exit(1)

def run_test(basename, reg, expected):
    """Run the test pipeline: ASM -> BIN -> Emulator"""
    asm_path = INPUT_DIR / f"{basename}.masm"
    bin_path = OUTPUT_DIR / f"{basename}.bin"
    log_path = OUTPUT_DIR / f"{basename}.log"

    results[basename] = []

    # Step 1: Assemble ASM -> BIN
    if run_step([str(ASM_PATH), str(asm_path), str(bin_path)], f"ASM to BIN: {basename}.masm", basename, log_path=log_path) is None:
        return

    # Step 2: Run Emulator
    output = run_step([str(EMU_PATH), "-i", str(bin_path), "--reg", reg], f"Run Emulator: {basename}.bin", basename, log_path=log_path)
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
    status_line("RUN", f"{1 if selected else len(testcases)} case(s)" if selected else f"{len(testcases)} case(s)")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if selected:
        matches = [t for t in testcases if t[0] == selected]
        if not matches:
            print(f"[ERROR] Test case '{selected}' not found.")
            sys.exit(1)
        to_run = matches
    else:
        to_run = testcases

    # Sequential execution keeps emulator stdout manageable and avoids timeouts.
    for t in to_run:
        run_test(*t)

    passed = 0
    failed = 0
    for name in sorted(results.keys()):
        if has_failure(results[name]):
            failed += 1
            summary = next((r for r in results[name] if r.startswith("❌")), "❌ failed")
            status_line("FAIL", f"{name} {summary.removeprefix('❌ ').strip()}", RED)
            for r in results[name]:
                if r.startswith("✅"):
                    continue
                print(f"  {r}")
        else:
            passed += 1
            summary = next((r for r in results[name] if r.startswith("✅")), "✅ PASS")
            status_line("PASS", f"{name} {summary.removeprefix('✅ ').strip()}", GREEN)
    status_line("DONE", f"Summary: {passed} passed, {failed} failed", GREEN if failed == 0 else YELLOW)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run assembler integration tests.")
    parser.add_argument("test", nargs="?", help="Optional test case name or source filename")
    parser.add_argument("--verbose", action="store_true", help="Show step-by-step command progress")
    args = parser.parse_args()

    VERBOSE = args.verbose

    if args.test:
        filename = args.test
        base, ext = os.path.splitext(filename)
        basename = base if ext else filename
    else:
        basename = None

    clean_all()
    build_all()
    run_tests(basename)
