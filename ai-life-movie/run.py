"""Simple startup entrypoint: `python run.py`."""
from __future__ import annotations

import os

import uvicorn

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    reload_enabled = os.environ.get("RELOAD", "false").lower() == "true"
    uvicorn.run("app.main:app", host=host, port=port, reload=reload_enabled)
