import os
import sys

# Ensure dashboard/backend is included in sys.path for module resolution
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
