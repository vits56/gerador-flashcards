from groq import Groq
import json
import time
from typing import List, Dict
from pydantic import BaseModel, ValidationError


class FlashcardSchema(BaseModel):
    pergunta: str
    resposta: str


class GroqFlashcardEngine:
    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = Groq(api_key=self.api_key)

        # IMPORTANT: response_format=json_object exige que o modelo retorne um OBJETO JSON ({}).
        # Por isso pedimos {"flashcards": [...]} — não uma lista diretamente.
        self.system_instruction = """Você é um professor especialista na criação de flashcards para provas de concursos públicos brasileiros.
Sua tarefa é analisar o texto fornecido e extrair ABSOLUTAMENTE TODAS as informações que possam ser alvo de questões de prova.
Você deve criar dezenas de flashcards abrangentes cobrindo:
- Regras gerais e suas exceções.
- Prazos, datas e penalidades.
- Definições teóricas, classificações e conceitos.
- Competências de órgãos, autoridades ou entes.
- Qualquer detalhe mnemônico ou pegadinha comum em provas.

Seja exaustivo: não deixe nenhum detalhe de fora.

Retorne APENAS um objeto JSON válido, sem texto adicional, com exatamente esta estrutura:
{
  "flashcards": [
    {
      "pergunta": "...",
      "resposta": "..."
    }
  ]
}"""

    def generate_flashcards(self, text_chunk: str) -> List[Dict[str, str]]:
        """
        Envia um bloco de texto para o Groq e retorna lista de dicts {pergunta, resposta}.
        Retorna lista vazia em caso de erro para isolar a falha sem quebrar o processo todo.
        """
        max_retries = 4
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.system_instruction},
                        {
                            "role": "user",
                            "content": (
                                "Crie o máximo de flashcards úteis possíveis "
                                "a partir do seguinte texto:\n\n" + text_chunk
                            )
                        }
                    ],
                    temperature=0.4,
                    response_format={"type": "json_object"},
                )

                output_text = response.choices[0].message.content
                parsed = json.loads(output_text)

                # Extrai a lista de flashcards — aceita tanto {"flashcards": [...]} quanto [...]
                if isinstance(parsed, list):
                    raw_flashcards = parsed
                elif isinstance(parsed, dict):
                    # Procura qualquer valor que seja uma lista
                    raw_flashcards = next(
                        (v for v in parsed.values() if isinstance(v, list)), []
                    )
                else:
                    print("Resposta do modelo em formato inesperado.")
                    return []

                # Valida estrutura com Pydantic
                valid_cards = []
                for card in raw_flashcards:
                    try:
                        validated = FlashcardSchema.model_validate(card)
                        valid_cards.append({
                            "pergunta": validated.pergunta,
                            "resposta": validated.resposta
                        })
                    except ValidationError:
                        continue  # Ignora cards mal formatados

                return valid_cards

            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON da resposta: {e}")
                return []

            except Exception as e:
                error_msg = str(e).lower()
                is_rate_limit = "429" in error_msg or "rate" in error_msg or "quota" in error_msg

                if is_rate_limit and attempt < max_retries - 1:
                    wait = 30 * (attempt + 1)
                    print(f"Rate limit atingido. Aguardando {wait}s... (tentativa {attempt + 1}/{max_retries})")
                    time.sleep(wait)
                    continue

                print(f"Erro na API Groq: {e}. Pulando este bloco.")
                return []

        return []
