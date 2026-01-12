import os
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path("/workspaces/MyComputer")
INPUT_DIR = ROOT_DIR / "MyTester/inputs/linker"
OUTPUT_DIR = ROOT_DIR / "MyTester/outputs/linker"

LINKER_DIR = ROOT_DIR / "MyLangLinker"
LINKER_EXE = LINKER_DIR / "mllinker"
OBJ_GEN = LINKER_DIR / "tools/obj_gen.py"

def colored(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

GREEN = "32"
RED = "31"
CYAN = "36"

def run_step(command, description):
    try:
        print(colored(f"[RUNNING] {description}:", CYAN), ' '.join(command))
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(colored(f"[OK] {description}", GREEN))
        if result.stdout.strip():
            print("STDOUT:", result.stdout.strip())
        return result
    except subprocess.CalledProcessError as e:
        print(colored(f"[ERROR] {description} failed!", RED))
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return None

def build_linker():
    print("[INFO] Building Linker...")
    if run_step(["make", "-C", str(LINKER_DIR), "clean", "all"], "Build MyLangLinker") is None:
        print(colored("Build failed. Exiting.", RED))
        sys.exit(1)

def run_test(test_name, json_inputs):
    print(f"\n--- Running Test: {test_name} ---")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    obj_files = []
    
    # 1. Generate Object Files
    for json_file in json_inputs:
        input_path = INPUT_DIR / json_file
        obj_name = json_file.replace(".json", ".obj")
        output_obj = OUTPUT_DIR / obj_name
        
        cmd = ["python3", str(OBJ_GEN), str(input_path), str(output_obj)]
        if run_step(cmd, f"Generate {obj_name}") is None:
            return False
        obj_files.append(str(output_obj))
        
    # 2. Link
    output_bin = OUTPUT_DIR / f"{test_name}.bin"
    cmd = [str(LINKER_EXE), str(output_bin)] + obj_files
    
    res = run_step(cmd, f"Link to {test_name}.bin")
    if res is None:
        return False
        
    print(colored(f"[SUCCESS] Test {test_name} passed!", GREEN))
    return True

if __name__ == "__main__":
    build_linker()
    
    # Define tests: Name -> List of JSON inputs
    tests = [
        ("test_basic", ["test_A.json", "test_B.json"]),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, inputs in tests:
        if run_test(name, inputs):
            passed += 1
            
    print(f"\nSummary: {passed}/{total} tests passed.")
    if passed != total:
        sys.exit(1)