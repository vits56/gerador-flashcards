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
from ai_engine import GroqFlashcardEngine, OllamaFlashcardEngine
from anki_builder import AnkiBuilder

# Configuração básica de aparência
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

GROQ_CONSOLE_URL = "https://console.groq.com/keys"

# Diretório de configuração do usuário (funciona tanto no .py quanto no .exe)
CONFIG_DIR = Path.home() / ".GeradorFlashcardsAnki"
CONFIG_FILE = CONFIG_DIR / "config.json"


class ApiKeyHelpWindow(ctk.CTkToplevel):
    """Janela flutuante com tutorial passo a passo de como obter a chave Groq."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Como obter sua chave gratuita do Groq")
        self.geometry("520x460")
        self.resizable(False, False)
        self.grab_set()
        self.focus()

        ctk.CTkLabel(
            self, text="🔑 Obtendo sua Chave da API do Groq",
            font=("Helvetica", 16, "bold")
        ).pack(pady=(20, 5), padx=20)

        ctk.CTkLabel(
            self, text="O Groq é gratuito — não precisa de cartão de crédito.",
            font=("Helvetica", 12), text_color="gray"
        ).pack(pady=(0, 10))

        steps_frame = ctk.CTkFrame(self)
        steps_frame.pack(pady=5, padx=20, fill="both", expand=True)

        steps = [
            ("1️⃣", "Clique no botão abaixo para abrir o site do Groq."),
            ("2️⃣", "Crie uma conta gratuita (pode usar sua conta Google)."),
            ("3️⃣", 'No menu lateral, clique em "API Keys".'),
            ("4️⃣", 'Clique em "Create API Key", dê qualquer nome e confirme.'),
            ("5️⃣", "Copie a chave gerada — ela começa com gsk_"),
            ("6️⃣", "Cole a chave no campo do aplicativo e clique em Gerar Flashcards."),
            ("✅", "A chave é salva automaticamente. Você só precisa fazer isso uma vez!"),
        ]

        for icon, text in steps:
            row = ctk.CTkFrame(steps_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=5)
            ctk.CTkLabel(row, text=icon, font=("Helvetica", 14), width=30, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=text, font=("Helvetica", 12), anchor="w", wraplength=400, justify="left").pack(side="left", padx=6)

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
        self.geometry("660x750")
        self.minsize(560, 650)   # Tamanho mínimo para a janela

        self.selected_pdf_path = None
        self._show_api_key = False  # Controla visibilidade da chave

        self.setup_ui()
        self.load_config()

    # ─── Configuração ──────────────────────────────────────────────
    def load_config(self):
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    if "api_key" in config:
                        self.api_key_var.set(config["api_key"])
                    if "model" in config and hasattr(self, "model_var"):
                        self.model_var.set(config["model"])
        except Exception as e:
            self.log(f"Aviso: não foi possível carregar config: {e}")

    def save_config(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "api_key": self.api_key_var.get().strip(),
                    "model": getattr(self, "model_var", ctk.StringVar(value="llama-3.3-70b-versatile")).get()
                }, f)
        except Exception as e:
            self.log(f"Aviso: não foi possível salvar config: {e}")

    # ─── Interface ─────────────────────────────────────────────────
    def setup_ui(self):
        # Título
        ctk.CTkLabel(
            self, text="Gerador de Flashcards Anki 🧠",
            font=("Helvetica", 22, "bold")
        ).pack(pady=(20, 10))

        # TabView PDF / Texto Livre
        self.tabview = ctk.CTkTabview(self, height=150)
        self.tabview.pack(pady=10, padx=20, fill="x")
        self.tabview.add("Arquivo PDF")
        self.tabview.add("Texto Livre")

        # --- Aba PDF ---
        self.btn_select_pdf = ctk.CTkButton(
            self.tabview.tab("Arquivo PDF"),
            text="📂 Selecionar PDF",
            command=self.select_pdf
        )
        self.btn_select_pdf.pack(pady=20)

        self.lbl_selected_file = ctk.CTkLabel(
            self.tabview.tab("Arquivo PDF"),
            text="Nenhum arquivo selecionado",
            text_color="gray"
        )
        self.lbl_selected_file.pack(pady=5)

        # --- Aba Texto ---
        self.entry_deck_title = ctk.CTkEntry(
            self.tabview.tab("Texto Livre"),
            placeholder_text="Título do Baralho (Opcional)"
        )
        self.entry_deck_title.pack(pady=(10, 5), padx=10, fill="x")

        self.textbox_input = ctk.CTkTextbox(self.tabview.tab("Texto Livre"), height=100)
        self.textbox_input.pack(pady=5, padx=10, fill="both", expand=True)
        self._setup_placeholder(self.textbox_input, "Cole o texto do seu resumo aqui...")

        # --- Seção de API Key ---
        api_frame = ctk.CTkFrame(self, fg_color="transparent")
        api_frame.pack(pady=(8, 2), padx=30, fill="x")

        ctk.CTkLabel(
            api_frame,
            text="Chave da API do Groq (gratuita, necessária para o app funcionar):",
            font=("Helvetica", 12, "bold"),
            anchor="w"
        ).pack(anchor="w")

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

        # Campo de API Key + botão olho
        key_row = ctk.CTkFrame(api_frame, fg_color="transparent")
        key_row.pack(fill="x")

        self.api_key_var = ctk.StringVar(value="")
        self.entry_api_key = ctk.CTkEntry(
            key_row,
            textvariable=self.api_key_var,
            show="*",
            placeholder_text="Cole sua chave de API aqui",
            height=36
        )
        self.entry_api_key.pack(side="left", fill="x", expand=True)

        self.btn_toggle_key = ctk.CTkButton(
            key_row,
            text="👁",
            width=40,
            height=36,
            fg_color="gray30",
            hover_color="gray20",
            command=self.toggle_api_key_visibility
        )
        self.btn_toggle_key.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(
            api_frame,
            text="🔒 Salva automaticamente no seu computador após o primeiro uso.",
            font=("Helvetica", 10),
            text_color="gray",
            anchor="w"
        ).pack(anchor="w", pady=(2, 0))

        # --- Seção de Seleção de Modelo ---
        model_frame = ctk.CTkFrame(self, fg_color="transparent")
        model_frame.pack(pady=(2, 10), padx=30, fill="x")

        ctk.CTkLabel(
            model_frame,
            text="🧠 Inteligência Artificial:",
            font=("Helvetica", 12, "bold")
        ).pack(side="left")

        self.model_var = ctk.StringVar(value="llama-3.3-70b-versatile")
        self.model_menu = ctk.CTkOptionMenu(
            model_frame,
            variable=self.model_var,
            values=[
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "Ollama: llama3.1"
            ],
            command=self.on_model_change
        )
        self.model_menu.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Botão Gerar
        self.btn_generate = ctk.CTkButton(
            self, text="⚡ Gerar Flashcards",
            command=self.start_generation_thread,
            height=45, font=("Helvetica", 15, "bold"),
            fg_color="#28a745", hover_color="#218838"
        )
        self.btn_generate.pack(pady=(16, 8))

        # Barra de Progresso
        self.progress_bar = ctk.CTkProgressBar(self, mode="determinate")
        self.progress_bar.pack(pady=6, fill="x", padx=40)
        self.progress_bar.set(0)

        # LogBox
        self.log_box = ctk.CTkTextbox(self, height=200, state="disabled")
        self.log_box.pack(pady=10, padx=20, fill="both", expand=True)

        # Chama inicialização do modelo
        self.on_model_change(self.model_var.get())

    def on_model_change(self, choice):
        if choice.startswith("Ollama"):
            self.entry_api_key.configure(state="disabled", placeholder_text="Ignorado para IA Local")
        else:
            self.entry_api_key.configure(state="normal", placeholder_text="Cole sua chave de API aqui")

    def _setup_placeholder(self, textbox: ctk.CTkTextbox, placeholder: str):
        """Adiciona comportamento de placeholder ao CTkTextbox."""
        textbox.insert("1.0", placeholder)
        textbox.configure(text_color="gray")

        def on_focus_in(event):
            if textbox.get("1.0", "end-1c") == placeholder:
                textbox.delete("1.0", "end")
                textbox.configure(text_color=("black", "white"))

        def on_focus_out(event):
            if not textbox.get("1.0", "end-1c").strip():
                textbox.insert("1.0", placeholder)
                textbox.configure(text_color="gray")

        textbox.bind("<FocusIn>", on_focus_in)
        textbox.bind("<FocusOut>", on_focus_out)

    def toggle_api_key_visibility(self):
        """Alterna entre mostrar e esconder a chave da API."""
        self._show_api_key = not self._show_api_key
        if self._show_api_key:
            self.entry_api_key.configure(show="")
            self.btn_toggle_key.configure(text="🙈")
        else:
            self.entry_api_key.configure(show="*")
            self.btn_toggle_key.configure(text="👁")

    def show_api_help(self):
        ApiKeyHelpWindow(self)

    # ─── Log (thread-safe) ─────────────────────────────────────────
    def log(self, message: str):
        """Agenda atualização do log na thread principal (thread-safe)."""
        self.after(0, self._log_safe, message)

    def _log_safe(self, message: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ─── Progresso (thread-safe) ───────────────────────────────────
    def update_progress(self, value: float):
        """Agenda atualização da barra de progresso na thread principal."""
        self.after(0, self.progress_bar.set, value)

    # ─── Seleção de PDF ────────────────────────────────────────────
    def select_pdf(self):
        filepath = filedialog.askopenfilename(
            title="Selecione um arquivo PDF de estudo",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if filepath:
            self.selected_pdf_path = filepath
            filename = os.path.basename(filepath)
            self.lbl_selected_file.configure(
                text=f"✅ Selecionado: {filename}", text_color="#4da6ff"
            )
            self.log(f"Arquivo selecionado: {filepath}")

    # ─── Geração de Flashcards ─────────────────────────────────────
    def start_generation_thread(self):
        """Valida campos antes de iniciar a thread de geração."""
        api_key = self.api_key_var.get().strip()
        is_ollama = self.model_var.get().startswith("Ollama")
        
        if not api_key and not is_ollama:
            messagebox.showerror(
                "Chave da API ausente",
                "Você precisa inserir sua chave do Groq para usar o app na nuvem.\n\n"
                "Clique no link azul para ver como obter a chave gratuita."
            )
            return

        active_tab = self.tabview.get()
        if active_tab == "Arquivo PDF" and not self.selected_pdf_path:
            messagebox.showerror("PDF não selecionado", "Selecione um arquivo PDF antes de gerar.")
            return

        if active_tab == "Texto Livre":
            placeholder = "Cole o texto do seu resumo aqui..."
            texto = self.textbox_input.get("1.0", "end-1c").strip()
            if not texto or texto == placeholder:
                messagebox.showerror("Texto vazio", "Cole um texto na aba 'Texto Livre' antes de gerar.")
                return

        # Desabilita controles
        self.btn_generate.configure(state="disabled", text="⏳ Gerando...")
        self.btn_select_pdf.configure(state="disabled")
        self.entry_api_key.configure(state="disabled")
        self.btn_toggle_key.configure(state="disabled")
        self.textbox_input.configure(state="disabled")
        self.model_menu.configure(state="disabled")
        self.update_progress(0)
        self.log("─" * 50)
        self.log("🚀 Iniciando geração de flashcards...")

        threading.Thread(target=self.process_content, daemon=True).start()

    def process_content(self):
        try:
            active_tab = self.tabview.get()
            deck_title = "Resumo_IA"
            chunks_with_images = []
            parser = None

            # 1. Obtenção do conteúdo
            if active_tab == "Arquivo PDF":
                self.log("📖 Lendo arquivo PDF e extraindo imagens (isso pode demorar em PDFs grandes)...")
                parser = PDFParser(self.selected_pdf_path)
                chunks_with_images = parser.extract_chunks_with_images(
                    chunk_size=8000,
                    progress_callback=self.log
                )

                filename = os.path.basename(self.selected_pdf_path)
                deck_title = os.path.splitext(filename)[0].replace(" ", "_")

                total_imgs = sum(len(c["images"]) for c in chunks_with_images)
                self.log(
                    f"📊 {parser.page_count} páginas | "
                    f"{parser.char_count:,} caracteres | "
                    f"{total_imgs} imagem(ns)"
                )

                if parser.char_count == 0:
                    self.log("⚠️ Aviso: 0 caracteres extraídos. Provável PDF escaneado (imagem).")

            else:
                self.log("📝 Lendo texto fornecido...")
                placeholder = "Cole o texto do seu resumo aqui..."
                full_text = self.textbox_input.get("1.0", "end-1c")
                if full_text.strip() == placeholder:
                    full_text = ""

                title_input = self.entry_deck_title.get().strip()
                if title_input:
                    deck_title = title_input.replace(" ", "_")

                helper_parser = PDFParser("")
                text_chunks = helper_parser.chunk_text(full_text, chunk_size=8000)
                chunks_with_images = [{"text": t, "images": []} for t in text_chunks]

            if not chunks_with_images:
                self.log("⚠️ Nenhum conteúdo extraído.")
                return

            total_chunks = len(chunks_with_images)
            self.log(f"📦 Conteúdo dividido em {total_chunks} bloco(s).")

            # 2. Salva a chave e cria o engine
            self.save_config()
            api_key = self.api_key_var.get().strip()
            model_name = self.model_var.get()
            
            if model_name.startswith("Ollama"):
                import urllib.request
                try:
                    urllib.request.urlopen("http://localhost:11434/", timeout=2)
                except:
                    self.log("❌ Erro: O Ollama não parece estar rodando no seu computador.")
                    self.after(0, lambda: messagebox.showerror("Ollama não detectado", "Certifique-se de que o Ollama está aberto e rodando no seu PC antes de usar a IA Local."))
                    return
                self.log(f"🤖 Iniciando processamento local com {model_name}...")
                engine = OllamaFlashcardEngine(model_name=model_name, log_callback=self.log)
            else:
                self.log(f"🤖 Iniciando processamento com Groq ({model_name})...")
                engine = GroqFlashcardEngine(api_key=api_key, model_name=model_name, log_callback=self.log)

            all_flashcards = []
            all_media_files = []
            image_counter = 0

            for i, chunk_data in enumerate(chunks_with_images):
                chunk_text = chunk_data["text"]
                chunk_images = chunk_data["images"]

                self.log(f"  🔄 Bloco {i+1}/{total_chunks}...")
                cards = engine.generate_flashcards(chunk_text)

                if cards:
                    if chunk_images:
                        img_bytes = chunk_images[0]
                        img_filename = f"img_{image_counter:04d}.png"
                        image_counter += 1
                        all_media_files.append((img_filename, img_bytes))
                        cards[0]["imagem_filename"] = img_filename
                        for card in cards[1:]:
                            card["imagem_filename"] = ""
                    else:
                        for card in cards:
                            card["imagem_filename"] = ""

                    all_flashcards.extend(cards)
                    self.log(f"     ✅ {len(cards)} flashcard(s) gerado(s).")
                else:
                    self.log(f"     ⚠️ Nenhum flashcard gerado para o bloco {i+1}.")

                self.update_progress((i + 1) / total_chunks)

                # Rate Limiting (Groq free tier)
                if i < total_chunks - 1:
                    time.sleep(2)

            # 3. Exportação
            if not all_flashcards:
                self.log("❌ Nenhum flashcard foi gerado no total.")
                return

            self.log(f"📦 Empacotando {len(all_flashcards)} flashcard(s)...")
            if all_media_files:
                self.log(f"   🖼️ {len(all_media_files)} imagem(ns) incluída(s).")

            builder = AnkiBuilder(deck_name=deck_title)

            downloads_path = Path.home() / "Downloads"
            downloads_path.mkdir(exist_ok=True)

            output_path = str(downloads_path / f"{deck_title}_Flashcards.apkg")
            report_path = str(downloads_path / f"{deck_title}_Relatorio.txt")

            builder.export_deck(
                all_flashcards,
                output_filename=output_path,
                media_files=all_media_files
            )

            # Relatório de texto
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"=== RELATÓRIO: {deck_title} ===\n")
                f.write(f"Total de flashcards: {len(all_flashcards)}\n")
                f.write(f"Imagens incluídas: {len(all_media_files)}\n")
                if parser:
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

            self.log("─" * 50)
            self.log("🎉 Sucesso! Arquivos salvos em Downloads:")
            self.log(f"   → {output_path}")
            self.log(f"   → {report_path}")

            total = len(all_flashcards)
            self.after(0, lambda: messagebox.showinfo(
                "Sucesso! 🎉",
                f"Foram gerados {total} flashcards!\n\n"
                f"Arquivo salvo em:\n{output_path}\n\n"
                "Abra o Anki e dê duplo clique no arquivo .apkg para importar!"
            ))

        except Exception as e:
            error_msg = f"ERRO: {str(e)}"
            self.log(f"❌ {error_msg}")
            self.after(0, lambda: messagebox.showerror("Erro", error_msg))

        finally:
            self.after(0, self._finish_processing_safe)

    def _finish_processing_safe(self):
        """Reabilita os controles — DEVE ser chamado na thread principal via after()."""
        self.btn_generate.configure(state="normal", text="⚡ Gerar Flashcards")
        self.btn_select_pdf.configure(state="normal")
        self.entry_api_key.configure(state="normal")
        self.btn_toggle_key.configure(state="normal")
        self.textbox_input.configure(state="normal")
        self.model_menu.configure(state="normal")
        self.log("✔️ Processamento finalizado.")
        self.log("─" * 50)


if __name__ == "__main__":
    app = FlashcardApp()
    app.mainloop()
