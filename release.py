"""
Script de build e publicação no GitHub Releases.

Uso:
    python release.py

O script:
  1. Lê a versão atual de version.txt
  2. Compila o .exe com PyInstaller
  3. Cria uma tag e um GitHub Release com o .exe como asset
  4. Usa o GitHub CLI (gh) — certifique-se de estar autenticado: gh auth login
"""

import subprocess
import sys
import os
import customtkinter

def read_version() -> str:
    with open("version.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

def build_exe():
    print("🔨 Compilando executável com PyInstaller...")
    customtkinter_path = os.path.dirname(customtkinter.__file__)
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "main.py",
        "--name=GeradorFlashcardsAnki",
        "--windowed",
        "--onefile",
        f"--add-data={customtkinter_path};customtkinter/",
        "--clean",
    ], check=True)
    print("✅ Build concluído.")

def create_github_release(version: str):
    exe_path = os.path.join("dist", "GeradorFlashcardsAnki.exe")
    if not os.path.exists(exe_path):
        print(f"❌ Executável não encontrado em: {exe_path}")
        sys.exit(1)

    tag = f"v{version}"
    title = f"Gerador de Flashcards Anki v{version}"
    notes = f"## v{version}\n\n- Baixe o arquivo `GeradorFlashcardsAnki.exe` abaixo e execute diretamente — não precisa instalar nada.\n"

    print(f"🚀 Criando GitHub Release {tag}...")
    subprocess.run([
        "gh", "release", "create", tag,
        exe_path,
        "--title", title,
        "--notes", notes,
        "--latest",
    ], check=True)
    print(f"✅ Release {tag} publicado no GitHub com sucesso!")

if __name__ == "__main__":
    version = read_version()
    print(f"📦 Versão: {version}")
    build_exe()
    create_github_release(version)
