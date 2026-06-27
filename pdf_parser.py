import fitz  # PyMuPDF
import re
from typing import List, Dict, Any

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
            raise Exception(f"Erro ao extrair texto do PDF: {str(e)}") from e

    def _extract_page_images(self, page: fitz.Page, doc: fitz.Document) -> List[bytes]:
        """
        Extrai imagens de uma página do PDF como bytes PNG.
        Filtra imagens muito pequenas (ícones/decorações) e imagens duplicadas.
        Retorna lista de bytes PNG.
        """
        MIN_AREA = 8000  # pixels² mínimos para considerar a imagem relevante
        seen_xrefs = set()
        images_bytes = []

        for img_info in page.get_images(full=True):
            xref = img_info[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)

            try:
                base_image = doc.extract_image(xref)
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)

                # Filtra imagens muito pequenas
                if width * height < MIN_AREA:
                    continue

                # Renderiza a imagem como PNG para garantir compatibilidade com o Anki
                img_bytes = base_image["image"]
                ext = base_image.get("ext", "png")

                # Se não for PNG ou JPEG, converte via renderização
                if ext.lower() not in ("png", "jpeg", "jpg"):
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n > 4:  # CMYK → RGB
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    img_bytes = pix.tobytes("png")

                images_bytes.append(img_bytes)
            except Exception:
                continue  # Ignora imagens corrompidas ou não suportadas

        return images_bytes

    def extract_chunks_with_images(self, chunk_size: int = 8000, progress_callback=None) -> List[Dict[str, Any]]:
        """
        Extrai texto e imagens do PDF em conjunto.
        Retorna lista de dicts: {'text': str, 'images': List[bytes]}
        Cada dict representa um chunk de texto com as imagens das páginas que o compõem.
        """
        if not self.filepath:
            return []

        try:
            doc = fitz.open(self.filepath)
            self.page_count = len(doc)

            # Extrai texto limpo e imagens por página
            pages_data = []
            for idx, page in enumerate(doc):
                if progress_callback:
                    progress_callback(f"📄 Lendo página {idx+1} de {self.page_count}...")
                
                page_text = page.get_text()
                lines = page_text.split('\n')
                cleaned_lines = []
                for line in lines:
                    stripped = line.strip()
                    if not stripped or stripped.isdigit():
                        continue
                    if re.match(r'(?i)^p[áa]gina\s+\d+(\s+de\s+\d+)?$', stripped):
                        continue
                    cleaned_lines.append(stripped)

                page_text_clean = " ".join(cleaned_lines)
                page_images = self._extract_page_images(page, doc)
                pages_data.append({"text": page_text_clean, "images": page_images})

            doc.close()

            # Agrupa páginas em chunks de texto, acumulando as imagens
            chunks = []
            current_text = ""
            current_images = []

            for page_data in pages_data:
                page_text = page_data["text"]
                page_imgs = page_data["images"]

                if len(current_text) + len(page_text) <= chunk_size:
                    current_text += page_text + " "
                    current_images.extend(page_imgs)
                else:
                    if current_text.strip():
                        chunks.append({
                            "text": current_text.strip(),
                            "images": current_images
                        })
                    current_text = page_text + " "
                    current_images = list(page_imgs)

            if current_text.strip():
                chunks.append({
                    "text": current_text.strip(),
                    "images": current_images
                })

            total_chars = sum(len(c["text"]) for c in chunks)
            self.char_count = total_chars
            return chunks

        except Exception as e:
            raise Exception(f"Erro ao extrair chunks com imagens do PDF: {str(e)}") from e

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
