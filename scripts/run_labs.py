#!/usr/bin/env python3
"""Run every lab (labs/NN-*/lab.py) in order and time each one.

Usage: python scripts/run_labs.py [--smoke] [--max-seconds N] [--only 05 07 ...] [--walkthroughs]

--walkthroughs runs the helper scripts in labs/walkthroughs/ instead of the numbered labs.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--max-seconds", type=float, default=0, help="fail any lab slower than this")
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--walkthroughs", action="store_true", help="run labs/walkthroughs/*.py")
    args = ap.parse_args()
    labs = sorted(ROOT.glob("labs/walkthroughs/*.py")) if args.walkthroughs else \
        sorted(ROOT.glob("labs/[0-9][0-9]-*/lab.py"))
    if args.only:
        labs = [p for p in labs if p.parent.name[:2] in args.only]
    failures = []
    t_all = time.time()
    # single-threaded BLAS: multi-threaded OpenBLAS can be ~100x slower on small eigh problems under load
    env = os.environ.copy()
    for var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        env.setdefault(var, "1")
    env.setdefault("MPLBACKEND", "Agg")
    for lab in labs:
        cmd = [sys.executable, str(lab)] + (["--smoke"] if args.smoke and not args.walkthroughs else [])
        t0 = time.time()
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)
        dt = time.time() - t0
        status = "ok" if res.returncode == 0 else f"FAILED (exit {res.returncode})"
        if res.returncode == 0 and args.max_seconds and dt > args.max_seconds:
            status = f"TOO SLOW (> {args.max_seconds:.0f}s)"
        name = lab.stem if args.walkthroughs else lab.parent.name
        print(f"{name:<45} {dt:6.1f}s  {status}")
        if status != "ok":
            failures.append(lab.parent.name)
            print(res.stdout[-2000:])
            print(res.stderr[-3000:])
    print(f"\n{len(labs)} labs in {time.time() - t_all:.0f}s, {len(failures)} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
