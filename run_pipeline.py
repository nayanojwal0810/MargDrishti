#!/usr/bin/env python
"""MargDrishti Pipeline Entrypoint.

Usage:
    python run_pipeline.py
"""

import sys
from pathlib import Path

# Add src to python path for direct execution
sys.path.insert(0, str(Path(__file__).parent / "src"))

from marg_drishti.pipeline import main

if __name__ == "__main__":
    main()
