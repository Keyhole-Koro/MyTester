#!/usr/bin/env python3
"""
Build and run the sample kernel from MyKernel using the toolchain:
  .ml -> .masm (mlc) -> .mbin/.mobj (myas) -> linked .mbin (mllinker) -> run (myemu)
"""

import argparse
import subprocess
from pathlib import Path


def run(cmd, cwd):
    print(f"+ {' '.join(str(c) for c in cmd)}")
    subprocess.check_call(cmd, cwd=cwd)


def main():
    parser = argparse.ArgumentParser(description="Build and run MyKernel sample.")
    parser.add_argument("--no-run", action="store_true", help="Build only; skip emulator run.")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    kernel_dir = repo / "MyKernel"
    build_dir = kernel_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    # Tool paths
    mlc = repo / "MyLangCompiler" / "mlc"
    myas = repo / "MyAssembler" / "build" / "myas"
    mllinker = repo / "MyLinker" / "mllinker"
    myemu = repo / "MyEmulator" / "build" / "myemu"

    # Sources
    kernel_ml = kernel_dir / "src" / "kernel_main.ml"
    helper_masm = kernel_dir / "asm" / "helper.masm"
    stub_masm = kernel_dir / "asm" / "stub.masm"
    boot_rom_src = repo / "MyEmulator" / "examples" / "boot_rom.masm"
    boot_rom_bin = repo / "MyEmulator" / "build" / "os" / "boot_rom.mbin"

    # Intermediate outputs
    kernel_masm = build_dir / "kernel_main.masm"
    kernel_mbin = build_dir / "kernel_main.mbin"
    kernel_mobj = build_dir / "kernel_main.mobj"

    helper_mbin = build_dir / "helper.mbin"
    helper_mobj = build_dir / "helper.mobj"

    stub_mbin = build_dir / "kernel_stub.mbin"
    stub_mobj = build_dir / "kernel_stub.mobj"

    linked_bin = build_dir / "kernel_linked.mbin"

    # Compile high-level kernel to MASM
    run([mlc, kernel_ml, kernel_masm], cwd=repo)

    # Assemble modules to .mbin/.mobj
    run([myas, kernel_masm, kernel_mbin, "--obj", kernel_mobj], cwd=repo)
    run([myas, helper_masm, helper_mbin, "--obj", helper_mobj], cwd=repo)
    run([myas, stub_masm, stub_mbin, "--obj", stub_mobj], cwd=repo)

    # Link all objects into final kernel image
    run([mllinker, linked_bin, stub_mobj, helper_mobj, kernel_mobj], cwd=repo)

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
