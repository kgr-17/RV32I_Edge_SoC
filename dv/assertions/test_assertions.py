#!/usr/bin/env python3
"""Reuse the independently checked random programs without altering them."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dv.random.test_random_programs import generate, REQUIRED_BINS, NEGATIVE_FULL_PROGRAM
NEGATIVE_DIAGNOSTIC = 'ASSERTIONS_MISMATCH fault'
