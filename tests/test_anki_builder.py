import pytest
import os
from anki_builder import AnkiBuilder

def test_create_note():
    builder = AnkiBuilder()
    note = builder._create_note("Pergunta teste", "Resposta teste")
    assert note is not None
    assert len(note.fields) == 2
    assert note.fields[0] == "Pergunta teste"
    assert note.fields[1] == "Resposta teste"

def test_export_deck(tmp_path):
    builder = AnkiBuilder()
    cards = [
        {"pergunta": "P1", "resposta": "R1"},
        {"pergunta": "P2", "resposta": "R2"}
    ]
    
    # Usar diretório temporário para não sujar o projeto com arquivos durante o teste
    output_file = tmp_path / "test_deck.apkg"
    
    builder.export_deck(cards, output_filename=str(output_file))
    
    assert os.path.exists(output_file)
    assert os.path.getsize(output_file) > 0

def test_export_deck_empty():
    builder = AnkiBuilder()
    with pytest.raises(ValueError):
        builder.export_deck([])
