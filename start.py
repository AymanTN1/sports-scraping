#!/usr/bin/env python3
"""
start.py — Script de démarrage principal de SportPulse
"""

from __future__ import annotations

import sys
import os
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.core import settings


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   ⚡ SPORTPULSE — VEILLE SPORTIVE IA ⚡                    ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    print(f"  📌 Nom du projet : {settings.project_name}")
    print(f"  📌 Version       : {settings.project_version}")
    print(f"  💾 Base de données: {settings.database_url}")
    print("  " + "─" * 60)
    print("  🖥️  Dashboard Web : http://127.0.0.1:8000/")
    print("  📖 API Swagger   : http://127.0.0.1:8000/api/docs")
    print("  📋 API ReDoc     : http://127.0.0.1:8000/redoc")
    print("  " + "─" * 60 + "\n")

    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
