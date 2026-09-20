"""Dispatch — Local Development Server Runner."""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.index import app as wsgi_app, run_local_server

# Top-level exports for WSGI runners
app = wsgi_app
application = wsgi_app

if __name__ == "__main__":
    run_local_server()
