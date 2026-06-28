import genanki
import random
import os
import re
import html
from typing import List, Dict, Tuple


def highlight_important(text: str) -> str:
    """
    Escapa o HTML do texto e envolve termos importantes em spans coloridos.
    - Números, datas, prazos, percentuais → vermelho
    - Palavras-chave jurídicas/técnicas → azul
    """
    # Primeiro escapa qualquer HTML que venha do texto da IA (< > & etc.)
    text = html.escape(text)

    # Números com unidades de prazo/valor → vermelho
    text = re.sub(
        r'\b(\d+(?:[.,]\d+)?(?:\s*(?:dias?|horas?|anos?|meses?|minutos?|segundos?|%|por\s+cento|reais?|R\$))?)\b',
        r'<span style="color:#e53935;font-weight:bold">\1</span>',
        text,
        flags=re.IGNORECASE
    )
    # Palavras-chave comuns em concursos → azul
    keywords = (
        r'\b(SEMPRE|NUNCA|OBRIGATÓRIO|OBRIGATÓRIA|VEDADO|VEDADA|EXCLUSIVO|EXCLUSIVA|'
        r'PROIBIDO|PROIBIDA|SOMENTE|APENAS|SALVO|EXCETO|RESSALVADO|'
        r'INCUMBE|COMPETE|CABE|DEVE|DEVERÁ|PODERÁ|FACULTATIVO|FACULTATIVA|'
        r'INCONSTITUCIONAL|CONSTITUCIONAL|NULO|NULA|ANULÁVEL|VICIADO)\b'
    )
    text = re.sub(
        keywords,
        r'<span style="color:#1976d2;font-weight:bold">\g<0></span>',
        text,
        flags=re.IGNORECASE
    )
    return text


class AnkiBuilder:
    def __init__(self, deck_name: str = "Flashcards Gerados via IA"):
        # Gera IDs únicos automáticos de 32-bits para o Model e para o Deck
        self.model_id = random.randrange(1 << 30, 1 << 31)
        self.deck_id = random.randrange(1 << 30, 1 << 31)
        self.deck_name = deck_name

        # CSS do cartão — suporta modo claro e modo noturno do Anki
        card_css = """
/* ── Modo claro (padrão) ── */
.card {
    font-family: 'Segoe UI', Arial, sans-serif;
    background-color: #ffffff;
    color: #111111;
    text-align: center;
    padding: 20px;
}
.pergunta {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 10px;
    color: #111111;
}
.resposta {
    font-size: 17px;
    color: #111111;
    margin-top: 10px;
    line-height: 1.6;
}

/* ── Modo noturno do Anki (nightMode) ── */
.nightMode .card {
    background-color: #1a1a1a;
    color: #ffffff;
}
.nightMode .pergunta {
    color: #ffffff;
}
.nightMode .resposta {
    color: #ffffff;
}
.nightMode hr#answer {
    border-top-color: #444;
}

/* ── Destaques de cores (funcionam em ambos os modos) ── */
.importante-vermelho {
    color: #e53935;
    font-weight: bold;
}
.importante-azul {
    color: #1565c0;
    font-weight: bold;
}
.nightMode .importante-azul {
    color: #64b5f6;
}

/* ── Imagem ── */
.card-image {
    max-width: 95%;
    max-height: 300px;
    object-fit: contain;
    margin-top: 16px;
    border-radius: 8px;
    border: 1px solid #cccccc;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    display: block;
    margin-left: auto;
    margin-right: auto;
}
.nightMode .card-image {
    border-color: #444;
}

/* ── Separador ── */
hr#answer {
    border: none;
    border-top: 2px solid #dddddd;
    margin: 18px 0;
}
"""
        # Template da frente: mostra apenas a pergunta
        frente = '<div class="pergunta">{{Pergunta}}</div>'

        # Template do verso: pergunta + linha + resposta + imagem (se houver)
        verso = """{{FrontSide}}
<hr id="answer">
<div class="resposta">{{Resposta}}</div>
{{#Imagem}}
<div style="text-align: center;">{{Imagem}}</div>
{{/Imagem}}"""

        # Criação do modelo de cartão do Anki (Pergunta / Resposta / Imagem opcional)
        self.model = genanki.Model(
            self.model_id,
            'Modelo Flashcard IA com Imagem',
            fields=[
                {'name': 'Pergunta'},
                {'name': 'Resposta'},
                {'name': 'Imagem'},   # Vazio quando não há imagem
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': frente,
                    'afmt': verso,
                },
            ],
            css=card_css
        )

        self.deck = genanki.Deck(self.deck_id, self.deck_name)

    def export_deck(
        self,
        cards_list: List[Dict],
        output_filename: str = "Flashcards_Gerados.apkg",
        media_files: List[Tuple[str, bytes]] = None
    ):
        """
        Recebe a lista de dicionários (perguntas, respostas e imagens opcionais)
        e exporta para um arquivo .apkg.

        cards_list: List de dicts com chaves 'pergunta', 'resposta',
                    e opcionalmente 'imagem_filename' (nome do arquivo de imagem).
        media_files: Lista de (filename, bytes) com as imagens a incluir no pacote.
        """
        if not cards_list:
            raise ValueError("A lista de flashcards fornecida está vazia.")

        if media_files is None:
            media_files = []

        # Salva os arquivos de mídia em um diretório temporário para o genanki
        temp_media_paths = []
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(output_filename)), "_anki_media_temp")
        if media_files:
            os.makedirs(temp_dir, exist_ok=True)
            for fname, fbytes in media_files:
                fpath = os.path.join(temp_dir, fname)
                with open(fpath, "wb") as f:
                    f.write(fbytes)
                temp_media_paths.append(fpath)

        for card_data in cards_list:
            pergunta = card_data.get("pergunta", "")
            resposta = card_data.get("resposta", "")
            imagem_fname = card_data.get("imagem_filename", "") or ""
            if imagem_fname:
                imagem_html = f'<img class="card-image" src="{imagem_fname}">'
            else:
                imagem_html = ""

            # Aplica destaques de palavras importantes
            pergunta_html = highlight_important(pergunta)
            resposta_html = highlight_important(resposta)

            if pergunta and resposta:
                note = genanki.Note(
                    model=self.model,
                    fields=[pergunta_html, resposta_html, imagem_html]
                )
                self.deck.add_note(note)

        # Empacota o deck com as mídias e escreve o arquivo final
        package = genanki.Package(self.deck)
        if temp_media_paths:
            package.media_files = temp_media_paths

        package.write_to_file(output_filename)

        # Limpa arquivos temporários de mídia
        for fpath in temp_media_paths:
            try:
                os.remove(fpath)
            except Exception:
                pass
        if temp_media_paths and os.path.isdir(temp_dir):
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass
