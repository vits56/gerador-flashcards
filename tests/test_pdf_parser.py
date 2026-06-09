import pytest
from pdf_parser import PDFParser
import os

def test_chunk_text():
    parser = PDFParser("dummy.pdf")
    text = "Esta é a primeira frase. Esta é a segunda frase. Esta é a terceira frase."
    
    # Se o chunk_size for pequeno, deve separar as frases
    chunks = parser.chunk_text(text, chunk_size=30)
    assert len(chunks) == 3
    assert chunks[0].strip() == "Esta é a primeira frase."
    assert chunks[1].strip() == "Esta é a segunda frase."
    assert chunks[2].strip() == "Esta é a terceira frase."

def test_chunk_text_large_size():
    parser = PDFParser("dummy.pdf")
    text = "Esta é a primeira frase. Esta é a segunda frase. Esta é a terceira frase."
    
    # Se o chunk_size for grande, tudo deve ficar em um único chunk
    chunks = parser.chunk_text(text, chunk_size=150)
    assert len(chunks) == 1
    assert "primeira frase" in chunks[0]
    assert "terceira frase" in chunks[0]
