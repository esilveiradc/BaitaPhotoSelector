"""
Baita Photo Selector v0.2-alpha

Launcher da v0.2-alpha baseado no codigo da v0.1-alpha.
Mantem a v0.1 intacta e aplica a nova identidade da versao.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tkinter as tk

BASE_DIR = Path(__file__).resolve().parent
LEGACY_FILE = BASE_DIR / "baita_photo_selector_pro_v0.1-alpha.py"

APP_NAME = "Baita Photo Selector"
APP_VERSION = "0.2-alpha"
RELATORIO_NOME = "relatorio_baita_photo_selector_v0_2_alpha.csv"


def carregar_modulo_v01():
    if not LEGACY_FILE.exists():
        raise FileNotFoundError(f"Arquivo base nao encontrado: {LEGACY_FILE}")

    spec = importlib.util.spec_from_file_location("baita_photo_selector_v01_alpha", LEGACY_FILE)
    if spec is None or spec.loader is None:
        raise ImportError("Nao foi possivel carregar o modulo base da v0.1-alpha.")

    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def main():
    modulo = carregar_modulo_v01()

    # Identidade da v0.2-alpha
    modulo.APP_NAME = APP_NAME
    modulo.APP_VERSION = APP_VERSION
    modulo.RELATORIO_NOME = RELATORIO_NOME

    root = tk.Tk()
    modulo.BaitaPhotoSelectorPro(root)
    root.mainloop()


if __name__ == "__main__":
    main()
