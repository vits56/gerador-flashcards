import PyInstaller.__main__
import os
import customtkinter

# Descobre o caminho da biblioteca customtkinter para incluir seus recursos (temas, fontes)
customtkinter_path = os.path.dirname(customtkinter.__file__)

PyInstaller.__main__.run([
    'main.py',
    '--name=GeradorFlashcardsAnki',
    '--windowed', # Oculta o console/terminal (apenas interface gráfica)
    '--onefile',  # Gera um único executável
    f'--add-data={customtkinter_path};customtkinter/', # Adiciona os assets do customtkinter
    '--clean',    # Limpa build anterior
])
