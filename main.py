import customtkinter as ctk
import threading
import time
from tkinter import filedialog
import os
import sys
import json
import tkinter.messagebox as messagebox
import webbrowser
from pathlib import Path

# Importações dos módulos locais
from pdf_parser import PDFParser
from ai_engine import GroqFlashcardEngine
from anki_builder import AnkiBuilder

# Configuração básica de aparência
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

GROQ_CONSOLE_URL = "https://console.groq.com/keys"

class ApiKeyHelpWindow(ctk.CTkToplevel):
    """Janela flutuante com tutorial passo a passo de como obter a chave Groq."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Como obter sua chave gratuita do Groq")
        self.geometry("520x460")
        self.resizable(False, False)
        self.grab_set()  # Bloqueia a janela principal enquanto esta está aberta
        self.focus()

        # Título
        ctk.CTkLabel(
            self, text="🔑 Obtendo sua Chave da API do Groq",
            font=("Helvetica", 16, "bold")
        ).pack(pady=(20, 5), padx=20)

        ctk.CTkLabel(
            self, text="O Groq é gratuito — não precisa de cartão de crédito.",
            font=("Helvetica", 12), text_color="gray"
        ).pack(pady=(0, 10))

        # Caixa com os passos
        steps_frame = ctk.CTkFrame(self)
        steps_frame.pack(pady=5, padx=20, fill="both", expand=True)

        steps = [
            ("1️⃣", "Clique no botão abaixo para abrir o site do Groq."),
            ("2️⃣", "Crie uma conta gratuita (pode usar sua conta Google)."),
            ("3️⃣", "No menu lateral, clique em \"API Keys\"."),
            ("4️⃣", "Clique em \"Create API Key\", dê qualquer nome e confirme."),
            ("5️⃣", "Copie a chave gerada — ela começa com gsk_"),
            ("6️⃣", "Cole a chave no campo do aplicativo e clique em Gerar Flashcards."),
            ("✅", "A chave é salva automaticamente. Você só precisa fazer isso uma vez!"),
        ]

        for icon, text in steps:
            row = ctk.CTkFrame(steps_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=5)
            ctk.CTkLabel(row, text=icon, font=("Helvetica", 14), width=30, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=text, font=("Helvetica", 12), anchor="w", wraplength=400, justify="left").pack(side="left", padx=6)

        # Botão para abrir o site
        ctk.CTkButton(
            self, text="🌐 Abrir console.groq.com/keys",
            command=lambda: webbrowser.open(GROQ_CONSOLE_URL),
            fg_color="#0070f3", hover_color="#0051a2",
            height=40, font=("Helvetica", 13, "bold")
        ).pack(pady=(10, 5), padx=30, fill="x")

        ctk.CTkButton(
            self, text="Fechar",
            command=self.destroy,
            fg_color="gray30", hover_color="gray20",
            height=36
        ).pack(pady=(0, 15), padx=30, fill="x")


class FlashcardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gerador de Flashcards Anki (Groq API)")
        self.geometry("650x730")
        self.config_file = "config.json"
        
        self.selected_pdf_path = None
        
        self.setup_ui()
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    if "api_key" in config:
                        self.api_key_var.set(config["api_key"])
            except Exception as e:
                self.log(f"Erro ao carregar config: {str(e)}")

    def save_config(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump({"api_key": self.api_key_var.get().strip()}, f)
        except Exception as e:
            self.log(f"Erro ao salvar config: {str(e)}")

    def setup_ui(self):
        # Título
        self.lbl_title = ctk.CTkLabel(self, text="Gerador de Flashcards (Concursos)", font=("Helvetica", 22, "bold"))
        self.lbl_title.pack(pady=(20, 10))
        
        # TabView para escolher entre PDF e Texto
        self.tabview = ctk.CTkTabview(self, height=150)
        self.tabview.pack(pady=10, padx=20, fill="x")
        self.tabview.add("Arquivo PDF")
        self.tabview.add("Texto Livre")
        
        # --- Aba PDF ---
        self.btn_select_pdf = ctk.CTkButton(self.tabview.tab("Arquivo PDF"), text="Selecionar PDF", command=self.select_pdf)
        self.btn_select_pdf.pack(pady=20)
        
        self.lbl_selected_file = ctk.CTkLabel(self.tabview.tab("Arquivo PDF"), text="Nenhum arquivo selecionado", text_color="gray")
        self.lbl_selected_file.pack(pady=5)
        
        # --- Aba Texto ---
        self.entry_deck_title = ctk.CTkEntry(self.tabview.tab("Texto Livre"), placeholder_text="Título do Baralho (Opcional)")
        self.entry_deck_title.pack(pady=(10, 5), padx=10, fill="x")
        
        self.textbox_input = ctk.CTkTextbox(self.tabview.tab("Texto Livre"), height=100)
        self.textbox_input.pack(pady=5, padx=10, fill="both", expand=True)
        self.textbox_input.insert("1.0", "Cole o texto do seu resumo aqui...")

        # --- Seção de API Key ---
        # Frame que agrupa label de ajuda + campo
        api_frame = ctk.CTkFrame(self, fg_color="transparent")
        api_frame.pack(pady=(8, 2), padx=30, fill="x")

        # Label explicativa com link clicável
        lbl_api_title = ctk.CTkLabel(
            api_frame,
            text="Chave da API do Groq (gratuita, necessária para o app funcionar):",
            font=("Helvetica", 12, "bold"),
            anchor="w"
        )
        lbl_api_title.pack(anchor="w")

        lbl_api_help = ctk.CTkLabel(
            api_frame,
            text="❓ Não sabe o que é isso? Clique aqui para ver como obter em 1 minuto →",
            font=("Helvetica", 11),
            text_color="#4da6ff",
            cursor="hand2",
            anchor="w"
        )
        lbl_api_help.pack(anchor="w", pady=(0, 4))
        lbl_api_help.bind("<Button-1>", lambda e: self.show_api_help())

        self.api_key_var = ctk.StringVar(value="")
        self.entry_api_key = ctk.CTkEntry(
            api_frame,
            textvariable=self.api_key_var,
            show="*",
            placeholder_text="Cole sua chave Groq aqui (começa com gsk_...)",
            height=36
        )
        self.entry_api_key.pack(fill="x")

        lbl_api_note = ctk.CTkLabel(
            api_frame,
            text="🔒 Salva automaticamente no seu computador após o primeiro uso.",
            font=("Helvetica", 10),
            text_color="gray",
            anchor="w"
        )
        lbl_api_note.pack(anchor="w", pady=(2, 0))

        # Botão Gerar
        self.btn_generate = ctk.CTkButton(
            self, text="Gerar Flashcards",
            command=self.start_generation_thread,
            height=45, font=("Helvetica", 15, "bold"),
            fg_color="#28a745", hover_color="#218838"
        )
        self.btn_generate.pack(pady=(16, 8))
        
        # Barra de Progresso
        self.progress_bar = ctk.CTkProgressBar(self, mode="determinate")
        self.progress_bar.pack(pady=6, fill="x", padx=40)
        self.progress_bar.set(0)
        
        # LogBox (Caixa de Texto de Status)
        self.log_box = ctk.CTkTextbox(self, height=200, state="disabled")
        self.log_box.pack(pady=10, padx=20, fill="both", expand=True)

    def show_api_help(self):
        """Abre a janela de tutorial de como obter a chave do Groq."""
        ApiKeyHelpWindow(self)

    def log(self, message: str):
        """Atualiza a LogBox de forma thread-safe e realiza o scroll automático."""
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        # Força atualização da interface (importante quando chamado por threads)
        self.update_idletasks()

    def select_pdf(self):
        filepath = filedialog.askopenfilename(
            title="Selecione um arquivo PDF de estudo",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if filepath:
            self.selected_pdf_path = filepath
            filename = os.path.basename(filepath)
            self.lbl_selected_file.configure(text=f"Selecionado: {filename}", text_color="white")
            self.log(f"Arquivo selecionado: {filepath}")

    def start_generation_thread(self):
        """Inicia o processamento em uma Thread para evitar o congelamento da GUI."""
        self.btn_generate.configure(state="disabled")
        self.btn_select_pdf.configure(state="disabled")
        self.entry_api_key.configure(state="disabled")
        self.textbox_input.configure(state="disabled")
        self.progress_bar.set(0)
        self.log("--- Iniciando Geração ---")
        
        # Roda o processo em Thread de background
        threading.Thread(target=self.process_pdf, daemon=True).start()

    def process_pdf(self):
        try:
            active_tab = self.tabview.get()
            deck_title = "Resumo_IA"
            # Chunks: List de {'text': str, 'images': List[bytes]} ou List de str (texto livre)
            chunks_with_images = []
            using_pdf = False

            # 1. Obtenção do conteúdo
            if active_tab == "Arquivo PDF":
                if not self.selected_pdf_path:
                    self.log("Erro: Nenhum PDF selecionado.")
                    self.finish_processing()
                    return

                self.log("Lendo arquivo PDF e extraindo imagens...")
                parser = PDFParser(self.selected_pdf_path)
                chunks_with_images = parser.extract_chunks_with_images(chunk_size=8000)

                filename = os.path.basename(self.selected_pdf_path)
                deck_title = os.path.splitext(filename)[0].replace(" ", "_")

                total_imgs = sum(len(c["images"]) for c in chunks_with_images)
                self.log(f"Metadados: {parser.page_count} páginas, {parser.char_count} caracteres, {total_imgs} imagem(ns) encontrada(s).")

                if parser.char_count == 0:
                    self.log("Aviso Crítico: 0 caracteres extraídos. Provável PDF escaneado (imagem).")

                using_pdf = True

            else:
                # Modo texto livre — sem imagens
                self.log("Lendo texto fornecido...")
                full_text = self.textbox_input.get("1.0", "end-1c")
                if full_text.strip() == "Cole o texto do seu resumo aqui...":
                    full_text = ""

                title_input = self.entry_deck_title.get().strip()
                if title_input:
                    deck_title = title_input.replace(" ", "_")

                if not full_text.strip():
                    self.log("Aviso: Nenhum texto foi fornecido ou extraído.")
                    self.finish_processing()
                    return

                helper_parser = PDFParser("")
                text_chunks = helper_parser.chunk_text(full_text, chunk_size=8000)
                chunks_with_images = [{"text": t, "images": []} for t in text_chunks]

            if not chunks_with_images:
                self.log("Aviso: Nenhum conteúdo foi extraído.")
                self.finish_processing()
                return

            total_chunks = len(chunks_with_images)
            self.log(f"Conteúdo dividido em {total_chunks} bloco(s) de processamento.")

            # 2. Validação da API Key
            api_key = self.api_key_var.get().strip()
            if not api_key:
                self.log("Erro: A API Key do Groq é obrigatória.")
                self.finish_processing()
                self.after(0, lambda: messagebox.showerror(
                    "Chave da API ausente",
                    "Você precisa inserir sua chave do Groq para usar o app.\n\n"
                    "Clique no link azul 'Como obter minha chave gratuita' na tela principal."
                ))
                return

            self.save_config()

            self.log("Iniciando processamento com Groq (Llama 3.3 70B)...")
            engine = GroqFlashcardEngine(api_key=api_key)

            all_flashcards = []
            all_media_files = []  # Lista de (filename, bytes)
            image_counter = 0

            for i, chunk_data in enumerate(chunks_with_images):
                chunk_text = chunk_data["text"]
                chunk_images = chunk_data["images"]

                self.log(f"Processando Bloco {i+1}/{total_chunks} no Groq...")
                cards = engine.generate_flashcards(chunk_text)

                if cards:
                    # Associa a primeira imagem do chunk (se houver) ao primeiro card do chunk
                    if chunk_images:
                        img_bytes = chunk_images[0]
                        img_filename = f"img_{image_counter:04d}.png"
                        image_counter += 1
                        all_media_files.append((img_filename, img_bytes))

                        # Primeiro card recebe a imagem; demais cards do mesmo chunk ficam sem imagem
                        cards[0]["imagem_filename"] = img_filename
                        for card in cards[1:]:
                            card["imagem_filename"] = ""
                    else:
                        for card in cards:
                            card["imagem_filename"] = ""

                    all_flashcards.extend(cards)
                    self.log(f"  -> {len(cards)} flashcard(s) gerado(s) neste bloco.")
                else:
                    self.log(f"  -> Nenhum flashcard válido gerado para o bloco {i+1}.")

                # Atualiza barra de progresso
                self.progress_bar.set((i + 1) / total_chunks)

                # Rate Limiting Preventivo (Groq free tier tem limites por minuto)
                if i < total_chunks - 1:
                    time.sleep(2)

            # 3. Geração do arquivo .apkg e relatório
            if not all_flashcards:
                self.log("Nenhum flashcard foi gerado no total.")
            else:
                self.log(f"Empacotando {len(all_flashcards)} flashcard(s)...")
                if all_media_files:
                    self.log(f"  -> Incluindo {len(all_media_files)} imagem(ns) no baralho.")

                builder = AnkiBuilder(deck_name=deck_title)

                output_file = f"{deck_title}_Flashcards.apkg"
                report_file = f"{deck_title}_Relatorio.txt"

                # Salva sempre na pasta Downloads do usuário para fácil acesso
                downloads_path = Path.home() / "Downloads"
                downloads_path.mkdir(exist_ok=True)

                output_path = str(downloads_path / output_file)
                report_path = str(downloads_path / report_file)

                # Gera o .apkg (com imagens, se houver)
                builder.export_deck(
                    all_flashcards,
                    output_filename=output_path,
                    media_files=all_media_files
                )

                # Gera o relatório de texto
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(f"=== RELATÓRIO DE GERAÇÃO: {deck_title} ===\n")
                    f.write(f"Total de flashcards gerados: {len(all_flashcards)}\n")
                    f.write(f"Imagens incluídas: {len(all_media_files)}\n")
                    if using_pdf:
                        parser_ref = PDFParser(self.selected_pdf_path)
                        f.write(f"Páginas analisadas: {parser.page_count}\n")
                        f.write(f"Caracteres extraídos: {parser.char_count}\n")
                    f.write("=" * 50 + "\n\n")

                    for idx, c in enumerate(all_flashcards, 1):
                        f.write(f"CARTÃO {idx}\n")
                        f.write(f"P: {c.get('pergunta', '')}\n")
                        f.write(f"R: {c.get('resposta', '')}\n")
                        if c.get("imagem_filename"):
                            f.write(f"Imagem: {c['imagem_filename']}\n")
                        f.write("-" * 40 + "\n")

                self.log("Sucesso! Arquivos salvos na pasta Downloads:")
                self.log(f" -> {output_path}")
                self.log(f" -> {report_path} (Leia para auditar o texto)")
                total = len(all_flashcards)
                self.after(0, lambda: messagebox.showinfo(
                    "Sucesso! 🎉",
                    f"Foram gerados {total} flashcards com sucesso!\n\n"
                    f"Arquivo salvo em:\n{output_path}\n\n"
                    "Abra o Anki e dê duplo clique no arquivo .apkg para importar!"
                ))

        except Exception as e:
            error_msg = f"ERRO CRÍTICO DURANTE EXECUÇÃO: {str(e)}"
            self.log(error_msg)
            self.after(0, lambda: messagebox.showerror("Erro Crítico", error_msg))

        finally:
            self.finish_processing()

    def finish_processing(self):
        # Reabilita botões após o processo
        self.btn_generate.configure(state="normal")
        self.btn_select_pdf.configure(state="normal")
        self.entry_api_key.configure(state="normal")
        self.textbox_input.configure(state="normal")
        self.log("--- Processamento Finalizado ---")

if __name__ == "__main__":
    app = FlashcardApp()
    app.mainloop()
