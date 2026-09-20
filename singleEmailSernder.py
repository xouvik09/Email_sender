"""Backward-compatible alias for singleEmailSender.py."""
import runpy
from pathlib import Path

target = Path(__file__).parent / "singleEmailSender.py"
runpy.run_path(str(target), run_name="__main__")
