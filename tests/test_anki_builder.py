import pytest
import os
import zipfile
from anki_builder import AnkiBuilder, highlight_important


def test_export_deck_basic(tmp_path):
    """Testa exportação básica sem imagens — campo imagem_filename vazio."""
    builder = AnkiBuilder()
    cards = [
        {"pergunta": "P1", "resposta": "R1", "imagem_filename": ""},
        {"pergunta": "P2", "resposta": "R2", "imagem_filename": ""},
    ]

    output_file = tmp_path / "test_deck.apkg"
    builder.export_deck(cards, output_filename=str(output_file))

    assert os.path.exists(output_file)
    assert os.path.getsize(output_file) > 0


def test_export_deck_with_images(tmp_path):
    """Testa exportação com imagem real — verifica que o .apkg contém o arquivo de mídia."""
    builder = AnkiBuilder()

    # Cria um PNG mínimo válido (1x1 pixel transparente)
    import struct, zlib
    def _minimal_png() -> bytes:
        sig = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
        ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
        ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
        raw = zlib.compress(b'\x00\x00\x00\x00')
        idat_crc = zlib.crc32(b'IDAT' + raw) & 0xffffffff
        idat = struct.pack('>I', len(raw)) + b'IDAT' + raw + struct.pack('>I', idat_crc)
        iend_crc = zlib.crc32(b'IEND') & 0xffffffff
        iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
        return sig + ihdr + idat + iend

    png_bytes = _minimal_png()
    img_filename = "img_0000.png"

    cards = [
        {"pergunta": "O que mostra a figura?", "resposta": "Um gráfico.", "imagem_filename": img_filename},
        {"pergunta": "P2", "resposta": "R2", "imagem_filename": ""},
    ]
    media_files = [(img_filename, png_bytes)]

    output_file = tmp_path / "test_deck_img.apkg"
    builder.export_deck(cards, output_filename=str(output_file), media_files=media_files)

    assert os.path.exists(output_file)
    # O .apkg é um ZIP; verifica que a imagem está dentro
    with zipfile.ZipFile(str(output_file), 'r') as zf:
        names = zf.namelist()
        # genanki embute mídias como "0", "1", etc. e um "media" JSON
        assert "media" in names, f"Arquivo 'media' não encontrado no .apkg. Conteúdo: {names}"


def test_export_deck_empty():
    """Testa que lista vazia levanta ValueError."""
    builder = AnkiBuilder()
    with pytest.raises(ValueError):
        builder.export_deck([])


def test_highlight_important_numbers():
    """Testa que números com unidades de prazo são destacados em vermelho."""
    result = highlight_important("O prazo é de 30 dias para recurso.")
    assert 'color:#e53935' in result
    assert '30 dias' in result


def test_highlight_important_keywords():
    """Testa que palavras-chave jurídicas são destacadas em azul."""
    result = highlight_important("É VEDADO ao servidor acumular cargos.")
    assert 'color:#1976d2' in result
    assert 'VEDADO' in result


def test_export_deck_missing_imagem_filename(tmp_path):
    """Testa que cards SEM a chave imagem_filename não crasham (defensivo)."""
    builder = AnkiBuilder()
    cards = [
        {"pergunta": "P1", "resposta": "R1"},  # Sem imagem_filename!
    ]

    output_file = tmp_path / "test_deck_no_img_key.apkg"
    builder.export_deck(cards, output_filename=str(output_file))

    assert os.path.exists(output_file)
    assert os.path.getsize(output_file) > 0
