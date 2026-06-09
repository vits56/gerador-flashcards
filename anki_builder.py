import genanki
import random
from typing import List, Dict

class AnkiBuilder:
    def __init__(self, deck_name: str = "Flashcards Gerados via IA"):
        # Gera IDs únicos automáticos de 32-bits para o Model e para o Deck
        self.model_id = random.randrange(1 << 30, 1 << 31)
        self.deck_id = random.randrange(1 << 30, 1 << 31)
        self.deck_name = deck_name
        
        # Criação do modelo de cartão do Anki (Front/Back)
        self.model = genanki.Model(
            self.model_id,
            'Modelo Flashcard IA',
            fields=[
                {'name': 'Pergunta'},
                {'name': 'Resposta'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '<div style="font-family: Arial; font-size: 20px; text-align: center;">{{Pergunta}}</div>',
                    'afmt': '{{FrontSide}}<hr id="answer"><div style="font-family: Arial; font-size: 18px; text-align: center; color: #005a9c;">{{Resposta}}</div>',
                },
            ],
            css='.card { background-color: #f9f9f9; text-align: center; color: black; }'
        )
        
        self.deck = genanki.Deck(self.deck_id, self.deck_name)

    def _create_note(self, question: str, answer: str) -> genanki.Note:
        """
        Cria uma nota individual do Anki com a pergunta e a resposta.
        """
        return genanki.Note(
            model=self.model,
            fields=[question, answer]
        )

    def export_deck(self, cards_list: List[Dict[str, str]], output_filename: str = "Flashcards_Gerados.apkg"):
        """
        Recebe a lista de dicionários (perguntas e respostas) e exporta para um arquivo .apkg.
        """
        if not cards_list:
            raise ValueError("A lista de flashcards fornecida está vazia.")
            
        for card_data in cards_list:
            pergunta = card_data.get("pergunta", "")
            resposta = card_data.get("resposta", "")
            
            if pergunta and resposta:
                note = self._create_note(pergunta, resposta)
                self.deck.add_note(note)
                
        # Empacota o deck e escreve o arquivo final
        package = genanki.Package(self.deck)
        package.write_to_file(output_filename)
