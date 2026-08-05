"""
run_pipeline.py - Execute tout le pipeline SportPulse en une commande.
Usage : python src/run_pipeline.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "src")
PY = sys.executable
PIPELINE_ENV = {
    **os.environ,
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
}


def run_step(name: str, script: str) -> None:
    print(f"\n{'=' * 55}")
    print(name)
    print(f"{'=' * 55}")
    start = time.time()
    result = subprocess.run([PY, os.path.join(SRC, script)], env=PIPELINE_ENV)
    elapsed = time.time() - start
    if result.returncode == 0:
        print(f"[OK] {name} termine en {elapsed:.1f}s")
        return

    print(f"[ERROR] Erreur dans {name} (code {result.returncode})")
    sys.exit(result.returncode)


if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("PIPELINE SPORTPULSE - VEILLE SPORTIVE MULTILINGUE")
    print("=" * 55)

    run_step("Scraping des sources", "scraper.py")
    run_step("Classification multilingue", "ai_organizer.py")
    run_step("Enrichissement (resumes+img)", "data_enricher.py")
    run_step("Verification des sources", "source_verifier.py")
    run_step("Generation des rapports", "report_generator.py")

    print("\n" + "=" * 55)
    print("PIPELINE TERMINE AVEC SUCCES")
    print("=" * 55)
    print("\nOuvrez : web/index.html dans votre navigateur")
    print("Ou lancez : python -m http.server 8000")
