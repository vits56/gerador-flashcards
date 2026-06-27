import genanki
import random
import os
from typing import List, Dict, Tuple

class AnkiBuilder:
    def __init__(self, deck_name: str = "Flashcards Gerados via IA"):
        # Gera IDs únicos automáticos de 32-bits para o Model e para o Deck
        self.model_id = random.randrange(1 << 30, 1 << 31)
        self.deck_id = random.randrange(1 << 30, 1 << 31)
        self.deck_name = deck_name

        # CSS do cartão
        card_css = """
.card {
    font-family: 'Segoe UI', Arial, sans-serif;
    background-color: #f9f9f9;
    color: #222;
    text-align: center;
    padding: 16px;
}
.pergunta {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 8px;
    color: #1a1a2e;
}
.resposta {
    font-size: 17px;
    color: #005a9c;
    margin-top: 8px;
}
.card-image {
    max-width: 95%;
    max-height: 280px;
    object-fit: contain;
    margin-top: 14px;
    border-radius: 6px;
    border: 1px solid #ddd;
    box-shadow: 0 2px 6px rgba(0,0,0,0.12);
}
hr#answer {
    border: none;
    border-top: 2px solid #ddd;
    margin: 16px 0;
}
"""
        # Template da frente: mostra apenas a pergunta
        frente = '<div class="pergunta">{{Pergunta}}</div>'

        # Template do verso: pergunta + linha + resposta + imagem (se houver)
        verso = """{{FrontSide}}
<hr id="answer">
<div class="resposta">{{Resposta}}</div>
{{#Imagem}}
<div><img class="card-image" src="{{Imagem}}"></div>
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
        temp_dir = os.path.join(os.path.dirname(output_filename), "_anki_media_temp")
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
            imagem_fname = card_data.get("imagem_filename", "")

            if pergunta and resposta:
                note = genanki.Note(
                    model=self.model,
                    fields=[pergunta, resposta, imagem_fname]
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
