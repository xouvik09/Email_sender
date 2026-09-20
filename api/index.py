"""Vercel Serverless Function entrypoint for Dispatch Email API."""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import EmailRequestHandler

# Vercel invokes `handler` as a BaseHTTPRequestHandler subclass
handler = EmailRequestHandler
