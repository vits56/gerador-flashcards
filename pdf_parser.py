import fitz  # PyMuPDF
import re

class PDFParser:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.page_count = 0
        self.char_count = 0

    def extract_text(self) -> str:
        """
        Extrai o texto do PDF, tentando remover numerações de página e cabeçalhos.
        """
        text = ""
        try:
            doc = fitz.open(self.filepath)
            self.page_count = len(doc)
            for page in doc:
                page_text = page.get_text()
                
                # Heurística básica de limpeza
                lines = page_text.split('\n')
                cleaned_lines = []
                for line in lines:
                    stripped_line = line.strip()
                    
                    # Ignora linhas vazias ou que contenham apenas números (prováveis números de página)
                    if not stripped_line or stripped_line.isdigit():
                        continue
                    
                    # Ignora padrões comuns de páginas como "Página 1", "Página 1 de 10"
                    if re.match(r'(?i)^p[áa]gina\s+\d+(\s+de\s+\d+)?$', stripped_line):
                        continue
                        
                    cleaned_lines.append(stripped_line)
                
                text += " ".join(cleaned_lines) + " "
            doc.close()
            final_text = text.strip()
            self.char_count = len(final_text)
            return final_text
        except Exception as e:
            raise Exception(f"Erro ao extrair texto do PDF: {str(e)}")

    def chunk_text(self, text: str, chunk_size: int = 3000) -> list[str]:
        """
        Divide o texto em blocos mantendo frases inteiras (não corta no meio da frase).
        """
        # Divide o texto por pontos finais seguidos de espaço para identificar frases
        sentences = re.split(r'(?<=\.)\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Se adicionar a próxima frase não ultrapassar o tamanho máximo do bloco
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + " "
            else:
                # Se o bloco atual já tem conteúdo, salva ele
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Inicia um novo bloco com a frase atual
                current_chunk = sentence + " "
        
        # Adiciona o último bloco se houver algo sobrando
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
