import pytest
from unittest.mock import patch, MagicMock
from ai_engine import GroqFlashcardEngine

def test_generate_flashcards_valid_json():
    engine = GroqFlashcardEngine(api_key="DUMMY_KEY")
    
    # Mock do retorno do Groq
    mock_response = MagicMock()
    mock_message = MagicMock()
    # Retorna uma lista correta que passará no Pydantic
    mock_message.content = '[\n{"pergunta": "Qual a capital do Brasil?", "resposta": "Brasília"}\n]'
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    
    with patch('groq.resources.chat.completions.Completions.create', return_value=mock_response):
        cards = engine.generate_flashcards("O Brasil é um país cuja capital é Brasília.")
        assert len(cards) == 1
        assert cards[0]["pergunta"] == "Qual a capital do Brasil?"
        assert cards[0]["resposta"] == "Brasília"

def test_generate_flashcards_invalid_pydantic_schema():
    engine = GroqFlashcardEngine(api_key="DUMMY_KEY")
    
    # Retorno com schema incorreto ("q" e "a" em vez de "pergunta" e "resposta")
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = '[\n{"q": "Qual a capital do Brasil?", "a": "Brasília"}\n]'
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    
    with patch('groq.resources.chat.completions.Completions.create', return_value=mock_response):
        cards = engine.generate_flashcards("O Brasil é um país cuja capital é Brasília.")
        # Pydantic vai dropar o card mal formatado e retornar lista vazia
        assert len(cards) == 0

def test_generate_flashcards_invalid_json():
    engine = GroqFlashcardEngine(api_key="DUMMY_KEY")
    
    # Retorno que não é JSON válido
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = 'Isso não é um JSON válido'
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    
    with patch('groq.resources.chat.completions.Completions.create', return_value=mock_response):
        cards = engine.generate_flashcards("Texto qualquer")
        assert len(cards) == 0
