import re
import ast

def patch_file():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Geometry
    content = re.sub(r'self\.geometry\("850x1100"\)', 'self.geometry("550x700")', content)
    content = re.sub(r'self\.minsize\(800,\s*1000\)', 'self.minsize(450, 650)', content)

    # 2. setup_ui
    setup_ui_new = '''    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("Light" if current == "Dark" else "Dark")

    def setup_ui(self):
        self.configure(fg_color=("#f3f4f6", "#1e1e1e"))
        
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # Cabeçalho
        header_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_bar.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(header_bar, text="Gerador de Flashcards Anki 🧠", font=("Segoe UI", 16, "bold")).pack(side="left")
        ctk.CTkButton(header_bar, text="☀️/🌙", width=40, height=24, font=("Segoe UI", 12), command=self.toggle_theme, fg_color="#444", hover_color="#555").pack(side="right")

        # CARD 1: Seleção de PDF
        card_file = ctk.CTkFrame(self.main_frame, fg_color=("#ffffff", "#2d2d2d"), corner_radius=6, border_width=1, border_color="#444")
        card_file.pack(fill="x", pady=(0, 6), ipady=10, ipadx=10)
        
        self.btn_select_pdf = ctk.CTkButton(card_file, text="📄 Selecionar PDF", command=self.select_pdf, fg_color="transparent", border_width=1, text_color=("black", "white"), font=("Segoe UI", 12))
        self.btn_select_pdf.pack(fill="x", padx=10, pady=(10, 0))
        
        self.lbl_selected_file = ctk.CTkLabel(card_file, text="Nenhum arquivo selecionado", text_color="gray", font=("Segoe UI", 11))
        self.lbl_selected_file.pack(pady=(2, 0))

        # CARD 2: API
        card_api = ctk.CTkFrame(self.main_frame, fg_color=("#ffffff", "#2d2d2d"), corner_radius=6, border_width=1, border_color="#444")
        card_api.pack(fill="x", pady=(0, 6), ipady=10, ipadx=10)
        
        ctk.CTkLabel(card_api, text="Chave da API do Groq:", font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x", padx=10)
        
        lbl_api_help = ctk.CTkLabel(card_api, text="❓ Obter chave da API (Gratuito) →", font=("Segoe UI", 11), text_color="#3b82f6", cursor="hand2", anchor="w")
        lbl_api_help.pack(fill="x", padx=10)
        lbl_api_help.bind("<Button-1>", lambda e: self.show_api_help())

        key_row = ctk.CTkFrame(card_api, fg_color="transparent")
        key_row.pack(fill="x", padx=10, pady=(5, 0))
        
        self.api_key_var = ctk.StringVar(value="")
        self.entry_api_key = ctk.CTkEntry(key_row, textvariable=self.api_key_var, show="*", height=28, font=("Segoe UI", 11))
        self.entry_api_key.pack(side="left", fill="x", expand=True)
        
        self.btn_toggle_key = ctk.CTkButton(key_row, text="👁", width=35, height=28, command=self.toggle_api_key_visibility, fg_color="#444", hover_color="#555")
        self.btn_toggle_key.pack(side="left", padx=(4, 0))

        # CARD 3: Motor IA
        card_model = ctk.CTkFrame(self.main_frame, fg_color=("#ffffff", "#2d2d2d"), corner_radius=6, border_width=1, border_color="#444")
        card_model.pack(fill="x", pady=(0, 6), ipady=10, ipadx=10)
        
        ctk.CTkLabel(card_model, text="Motor de IA", font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x", padx=10)
        
        self.model_var = ctk.StringVar(value="llama-3.3-70b-versatile")
        
        self.rb_fast = ctk.CTkRadioButton(card_model, text="⚡ Econômico (8B)", variable=self.model_var, value="llama-3.1-8b-instant", font=("Segoe UI", 11, "bold"))
        self.rb_fast.pack(anchor="w", padx=10, pady=(5, 0))
        ctk.CTkLabel(card_model, text="• Ideal para revisões rápidas e conceitos diretos.", font=("Segoe UI", 9), text_color="#888", anchor="w").pack(anchor="w", padx=30, pady=(0, 5))
        
        self.rb_advanced = ctk.CTkRadioButton(card_model, text="🧠 Avançado (70B)", variable=self.model_var, value="llama-3.3-70b-versatile", font=("Segoe UI", 11, "bold"))
        self.rb_advanced.pack(anchor="w", padx=10)
        ctk.CTkLabel(card_model, text="• Alta precisão para leis complexas e doutrinas.", font=("Segoe UI", 9), text_color="#888", anchor="w").pack(anchor="w", padx=30)

        # Botão Gerar
        self.btn_generate = ctk.CTkButton(self.main_frame, text="⏳ Gerar Flashcards", command=self.start_generation_thread, height=40, font=("Segoe UI", 13, "bold"), fg_color="#22c55e", hover_color="#16a34a")
        self.btn_generate.pack(fill="x", pady=(8, 8))

        # Terminal
        self.log_box = ctk.CTkTextbox(self.main_frame, height=100, state="disabled", fg_color="#000000", text_color="#10b981", font=("Consolas", 11), wrap="word", corner_radius=6)
        self.log_box.pack(fill="both", expand=True)

        self.progress_bar = ctk.CTkProgressBar(self.main_frame, mode="determinate", height=12)
        self.progress_bar.pack(fill="x", pady=(8, 0))
        self.progress_bar.set(0)
'''

    # Find bounds of setup_ui to _setup_placeholder inclusive
    lines = content.split('\n')
    setup_start = -1
    setup_end = -1
    for node in ast.parse(content).body:
        if isinstance(node, ast.ClassDef):
            for n in node.body:
                if isinstance(n, ast.FunctionDef) and n.name == 'setup_ui':
                    setup_start = n.lineno - 1
                if isinstance(n, ast.FunctionDef) and n.name == '_setup_placeholder':
                    setup_end = n.end_lineno

    if setup_start != -1 and setup_end != -1:
        lines = lines[:setup_start] + setup_ui_new.split('\n') + lines[setup_end:]
    
    content = '\n'.join(lines)

    # 3. start_generation_thread
    start_gen_old = '''    def start_generation_thread(self):
        """Valida campos antes de iniciar a thread de geração."""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror(
                "Chave da API ausente",
                "Você precisa inserir sua chave do Groq para usar o app.\n\n"
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
        self.rb_fast.configure(state="disabled")
        self.rb_advanced.configure(state="disabled")'''
    start_gen_new = '''    def start_generation_thread(self):
        """Valida campos antes de iniciar a thread de geração."""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror(
                "Chave da API ausente",
                "Você precisa inserir sua chave do Groq para usar o app.\n\n"
                "Clique no link azul para ver como obter a chave gratuita."
            )
            return

        if not self.selected_pdf_path:
            messagebox.showerror("PDF não selecionado", "Selecione um arquivo PDF antes de gerar.")
            return

        # Desabilita controles
        self.btn_generate.configure(state="disabled", text="⏳ Gerando...")
        self.btn_select_pdf.configure(state="disabled")
        self.entry_api_key.configure(state="disabled")
        self.btn_toggle_key.configure(state="disabled")
        self.rb_fast.configure(state="disabled")
        self.rb_advanced.configure(state="disabled")'''
    content = content.replace(start_gen_old, start_gen_new)

    # 4. process_content logic (removing tabview checks)
    process_content_old = '''    def process_content(self):
        try:
            active_tab = self.tabview.get()
            deck_title = "Resumo_IA"
            text_chunks = []
            parser = None

            # 1. Obtenção do conteúdo
            if active_tab == "Arquivo PDF":
                self.log("📖 Lendo arquivo PDF...")
                parser = PDFParser(self.selected_pdf_path)
                full_text = parser.extract_text()
                text_chunks = parser.chunk_text(full_text, chunk_size=3000)

                filename = os.path.basename(self.selected_pdf_path)
                deck_title = os.path.splitext(filename)[0].replace(" ", "_")

                self.log(
                    f"📊 {parser.page_count} páginas | "
                    f"{parser.char_count:,} caracteres"
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
                text_chunks = helper_parser.chunk_text(full_text, chunk_size=3000)'''

    process_content_new = '''    def process_content(self):
        try:
            deck_title = "Resumo_IA"
            text_chunks = []
            parser = None

            # 1. Obtenção do conteúdo
            self.log("📖 Lendo arquivo PDF...")
            parser = PDFParser(self.selected_pdf_path)
            full_text = parser.extract_text()
            text_chunks = parser.chunk_text(full_text, chunk_size=3000)

            filename = os.path.basename(self.selected_pdf_path)
            deck_title = os.path.splitext(filename)[0].replace(" ", "_")

            self.log(
                f"📊 {parser.page_count} páginas | "
                f"{parser.char_count:,} caracteres"
            )

            if parser.char_count == 0:
                self.log("⚠️ Aviso: 0 caracteres extraídos. Provável PDF escaneado (imagem).")'''
    content = content.replace(process_content_old, process_content_new)

    # 5. _finish_processing_safe (removing textbox_input)
    finish_processing_old = '''    def _finish_processing_safe(self, log_msg, err=None, err_type=None):
        self.btn_generate.configure(state="normal", text="⏳ Gerar Flashcards")
        self.btn_select_pdf.configure(state="normal")
        self.entry_api_key.configure(state="normal")
        self.btn_toggle_key.configure(state="normal")
        self.textbox_input.configure(state="normal")
        self.rb_fast.configure(state="normal")
        self.rb_advanced.configure(state="normal")'''
    finish_processing_new = '''    def _finish_processing_safe(self, log_msg, err=None, err_type=None):
        self.btn_generate.configure(state="normal", text="⏳ Gerar Flashcards")
        self.btn_select_pdf.configure(state="normal")
        self.entry_api_key.configure(state="normal")
        self.btn_toggle_key.configure(state="normal")
        self.rb_fast.configure(state="normal")
        self.rb_advanced.configure(state="normal")'''
    content = content.replace(finish_processing_old, finish_processing_new)

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    patch_file()
