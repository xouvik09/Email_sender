"""Dispatch — Local Server Runner."""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.index import handler, run_local_server

# Top-level exports for scanners
EmailRequestHandler = handler
app = handler
application = handler

if __name__ == "__main__":
    run_local_server()
