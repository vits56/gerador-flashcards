import pytest
from pdf_parser import PDFParser


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


def test_chunk_text_empty():
    """Testa que texto vazio retorna lista vazia."""
    parser = PDFParser("dummy.pdf")
    chunks = parser.chunk_text("", chunk_size=100)
    assert len(chunks) == 0 or all(c.strip() == "" for c in chunks)


def test_chunk_text_single_sentence():
    """Testa que uma frase menor que o chunk_size fica em um único chunk."""
    parser = PDFParser("dummy.pdf")
    text = "Frase única curta."
    chunks = parser.chunk_text(text, chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0].strip() == "Frase única curta."


def test_extract_chunks_empty_filepath():
    """Testa que filepath vazio retorna lista vazia sem crashar."""
    parser = PDFParser("")
    result = parser.extract_chunks_with_images()
    assert result == []
