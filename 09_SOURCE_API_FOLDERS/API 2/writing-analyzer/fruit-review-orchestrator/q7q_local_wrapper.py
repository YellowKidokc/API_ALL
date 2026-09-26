#!/usr/bin/env python3
"""Wrapper entrypoint that executes chi_evaluator_7q as a package module."""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("PYTHONPATH", BASE_DIR)

cmd = [sys.executable, "-m", "q7q_local.chi_evaluator_7q", *sys.argv[1:]]
os.execv(sys.executable, cmd)
