#!/usr/bin/env python3
"""
Build and run the sample kernel from MyKernel using the toolchain:
  .ml -> .masm (mlc) -> .mbin/.mobj (myas) -> linked .mbin (mllinker) -> run (myemu)
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.project_paths import (
    MYASSEMBLER_DIR,
    MYEMULATOR_DIR,
    MYKERNEL_DIR,
    MYLANGCOMPILER_DIR,
    MYLINKER_DIR,
    MYTESTER_DIR,
    REPO_ROOT,
)


def run(cmd, cwd):
    print(f"+ {' '.join(str(c) for c in cmd)}")
    subprocess.check_call(cmd, cwd=cwd)


def main():
    parser = argparse.ArgumentParser(description="Build and run MyKernel sample.")
    parser.add_argument("--no-run", action="store_true", help="Build only; skip emulator run.")
    args = parser.parse_args()

    repo = REPO_ROOT
    kernel_dir = MYKERNEL_DIR
    build_dir = kernel_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    # Tool paths
    mlc = MYLANGCOMPILER_DIR / "mlc"
    myas = MYASSEMBLER_DIR / "build" / "myas"
    mllinker = MYLINKER_DIR / "mllinker"
    myemu = MYEMULATOR_DIR / "build" / "myemu"

    # Sources
    kernel_ml = kernel_dir / "src" / "kernel_main.ml"
    stub_masm = kernel_dir / "asm" / "stub.masm"
    boot_rom_src = MYEMULATOR_DIR / "examples" / "boot_rom.masm"
    boot_rom_bin = MYEMULATOR_DIR / "build" / "os" / "boot_rom.mbin"

    linked_bin = build_dir / "kernel_linked.mbin"

    build_toolchain = MYTESTER_DIR / "build_toolchain.py"

    # Build kernel using toolchain script (stub must be first for entry point)
    run([
        sys.executable, build_toolchain,
        stub_masm, kernel_ml,
        "-o", linked_bin,
        "--build-dir", build_dir
    ], cwd=repo)

    # Ensure ROM image exists
    boot_rom_bin.parent.mkdir(parents=True, exist_ok=True)
    if not boot_rom_bin.exists():
        run([myas, boot_rom_src, boot_rom_bin], cwd=repo)

    if args.no_run:
        print("Build complete; skipping emulator run (--no-run).")
        return

    # Run emulator
    run([myemu, "--rom", boot_rom_bin, "--ram", linked_bin], cwd=repo)
    print("Done. See memory_dump.txt for RAM snapshot and emulator output above.")


if __name__ == "__main__":
    main()
