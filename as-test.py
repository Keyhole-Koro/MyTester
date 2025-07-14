import subprocess
import os
import sys

INPUT_DIR = "inputs"
OUTPUT_DIR = "outputs"

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

testcases = [
    #("simpleFunc.masm", "simpleFunc.bin"),
    ("simpleCondition.masm", "simpleCondition.bin"),
]

def rel_to_subproj(path):
    return f"../MyTester/{path}"

def run_step(cmd, stepname):
    try:
        print(f"\n[RUNNING] {stepname}: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print(f"[OK] {stepname}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] {stepname} failed!")
        print(f"  Command: {' '.join(cmd)}")
        print(f"  Return code: {e.returncode}")
        if e.stdout:
            print(f"  STDOUT:\n{e.stdout}")
        if e.stderr:
            print(f"  STDERR:\n{e.stderr}")
        sys.exit(1)

for asm_out, bin_out in testcases:
    asm_path = os.path.join(INPUT_DIR, asm_out)
    bin_path = os.path.join(OUTPUT_DIR, bin_out)

    asm_path_rel = rel_to_subproj(asm_path)
    bin_path_rel = rel_to_subproj(bin_path)

    run_step(["make", "-C", "../MyAssembler", "clean"], "MyAssembler clean")
    run_step(["make", "-C", "../MyAssembler", "run-myas", f"IN={asm_path_rel}", f"OUT={bin_path_rel}"], "ASM to BIN")

    run_step(["make", "-C", "../MyEmulator", "clean"], "MyEmulator clean")
    run_step(["make", "-C", "../MyEmulator", "run-myemu", f"IN={bin_path_rel}"], "BIN to Emulate")

print("\nAll tests passed🎉")
