import customtkinter as ctk
import threading
import time
from tkinter import filedialog
import os
import sys
import json
import tkinter.messagebox as messagebox

# Importações dos módulos locais
from pdf_parser import PDFParser
from ai_engine import GroqFlashcardEngine
from anki_builder import AnkiBuilder

# Configuração básica de aparência
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class FlashcardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gerador de Flashcards Anki (Gemini API)")
        self.geometry("650x700")
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
        
        # Campo para API Key
        self.api_key_var = ctk.StringVar(value="")
        self.entry_api_key = ctk.CTkEntry(self, textvariable=self.api_key_var, show="*", width=300, placeholder_text="Cole sua Groq API Key aqui (gsk_...)")
        self.entry_api_key.pack(pady=5)
        
        # Botão Gerar (agora sempre ativo pois pode gerar de texto livre)
        self.btn_generate = ctk.CTkButton(self, text="Gerar Flashcards", 
                                          command=self.start_generation_thread, 
                                          height=45, font=("Helvetica", 15, "bold"),
                                          fg_color="#28a745", hover_color="#218838")
        self.btn_generate.pack(pady=(20, 10))
        
        # Barra de Progresso
        self.progress_bar = ctk.CTkProgressBar(self, mode="determinate")
        self.progress_bar.pack(pady=10, fill="x", padx=40)
        self.progress_bar.set(0)
        
        # LogBox (Caixa de Texto de Status)
        self.log_box = ctk.CTkTextbox(self, height=200, state="disabled")
        self.log_box.pack(pady=10, padx=20, fill="both", expand=True)

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
            # 1. Obtenção do Texto (PDF ou Texto Livre)
            active_tab = self.tabview.get()
            full_text = ""
            deck_title = "Resumo_IA"
            
            if active_tab == "Arquivo PDF":
                if not self.selected_pdf_path:
                    self.log("Erro: Nenhum PDF selecionado.")
                    self.finish_processing()
                    return
                    
                self.log("Lendo arquivo PDF...")
                parser = PDFParser(self.selected_pdf_path)
                full_text = parser.extract_text()
                
                # Nome do baralho será o nome do arquivo PDF (sem extensão)
                filename = os.path.basename(self.selected_pdf_path)
                deck_title = os.path.splitext(filename)[0].replace(" ", "_")
                
                self.log(f"Metadados: Lidas {parser.page_count} páginas e {parser.char_count} caracteres.")
                if parser.char_count == 0:
                    self.log("Aviso Crítico: 0 caracteres extraídos. Provável PDF escaneado (imagem).")
                    
            else:
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

            # Utiliza o parser apenas para a função de chunking (não depende do path)
            parser = PDFParser("")
            chunks = parser.chunk_text(full_text, chunk_size=8000)
            total_chunks = len(chunks)
            self.log(f"PDF dividido em {total_chunks} blocos de processamento.")
            
            # 2. Processamento IA (Gemini)
            api_key = self.api_key_var.get().strip()
            if not api_key:
                self.log("Erro: A API Key do Groq é obrigatória.")
                self.finish_processing()
                # Run messagebox in main thread
                self.after(0, lambda: messagebox.showerror("Erro", "A API Key do Groq é obrigatória!"))
                return
            
            # Salva a chave para as próximas vezes
            self.save_config()

            self.log("Iniciando processamento com Groq (Llama 3.3 70B)...")
            engine = GroqFlashcardEngine(api_key=api_key)
            all_flashcards = []
            
            for i, chunk in enumerate(chunks):
                self.log(f"Processando Bloco {i+1}/{total_chunks} no Gemini...")
                cards = engine.generate_flashcards(chunk)
                if cards:
                    all_flashcards.extend(cards)
                    self.log(f"  -> {len(cards)} flashcards gerados neste bloco.")
                else:
                    self.log(f"  -> Nenhum flashcard válido gerado para o bloco {i+1}.")
                
                # Atualiza barra de progresso
                progress = (i + 1) / total_chunks
                self.progress_bar.set(progress)
                
                # Rate Limiting Preventivo (Gemini free = 15 RPM, ~1 req a cada 4 seg)
                if i < total_chunks - 1:
                    time.sleep(4.5)
            
            # 3. Geração do Arquivo Anki (.apkg) e Relatório
            if not all_flashcards:
                self.log("Nenhum flashcard foi gerado no total.")
            else:
                self.log(f"Empacotando {len(all_flashcards)} flashcards...")
                builder = AnkiBuilder(deck_name=deck_title)
                
                output_file = f"{deck_title}_Flashcards.apkg"
                report_file = f"{deck_title}_Relatorio.txt"
                
                # Salva o arquivo na mesma pasta do executável/script, mesmo em ambiente "frozen" (PyInstaller)
                if getattr(sys, 'frozen', False):
                    application_path = os.path.dirname(sys.executable)
                else:
                    application_path = os.path.dirname(os.path.abspath(__file__))
                
                output_path = os.path.join(application_path, output_file)
                report_path = os.path.join(application_path, report_file)
                
                # Gera o apkg
                builder.export_deck(all_flashcards, output_filename=output_path)
                
                # Gera o Relatório
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(f"=== RELATÓRIO DE GERAÇÃO: {deck_title} ===\n")
                    f.write(f"Total de flashcards gerados: {len(all_flashcards)}\n")
                    if active_tab == "Arquivo PDF":
                        f.write(f"Páginas analisadas: {parser.page_count}\n")
                        f.write(f"Caracteres extraídos: {parser.char_count}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for idx, c in enumerate(all_flashcards, 1):
                        f.write(f"CARTÃO {idx}\n")
                        f.write(f"P: {c.get('pergunta', '')}\n")
                        f.write(f"R: {c.get('resposta', '')}\n")
                        f.write("-" * 40 + "\n")
                        
                self.log(f"Sucesso! Arquivos criados:")
                self.log(f" -> {output_file}")
                self.log(f" -> {report_file} (Leia para auditar o texto)")
                self.after(0, lambda: messagebox.showinfo("Sucesso", f"Foram gerados {len(all_flashcards)} flashcards com sucesso!\n\nSalvo como: {output_file}"))
                
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
