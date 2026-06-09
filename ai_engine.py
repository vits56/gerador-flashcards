from groq import Groq
import json
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
        
        self.system_instruction = """Você é um professor especialista na criação de flashcards para provas de concursos públicos brasileiros.
Sua tarefa é analisar o texto fornecido e extrair ABSOLUTAMENTE TODAS as informações que possam ser alvo de questões de prova.
Você deve criar dezenas de flashcards abrangentes cobrindo:
- Regras gerais e suas exceções.
- Prazos, datas e penalidades.
- Definições teóricas, classificações e conceitos.
- Competências de órgãos, autoridades ou entes.
- Qualquer detalhe mnemônico ou pegadinha comum em provas.

Importante: Não resuma muito, seja exaustivo na criação dos flashcards para que nenhum detalhe da matéria fique de fora.

Retorne APENAS o JSON, sem nenhum texto adicional, usando exatamente este schema:
[
  {
    "pergunta": "...",
    "resposta": "..."
  }
]"""

    def generate_flashcards(self, text_chunk: str) -> List[Dict[str, str]]:
        """
        Envia um bloco de texto para o Groq e retorna uma lista de dicionários com pergunta/resposta.
        Em caso de erro crítico ou limite de taxa não recuperável, retorna lista vazia para isolar a falha.
        """
        import time
        max_retries = 4
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.system_instruction},
                        {"role": "user", "content": f"Crie o máximo de flashcards úteis possíveis a partir do seguinte texto:\n\n{text_chunk}"}
                    ],
                    temperature=0.4,
                    response_format={"type": "json_object"},
                )
                
                output_text = response.choices[0].message.content
                
                parsed = json.loads(output_text)
                
                if isinstance(parsed, list):
                    raw_flashcards = parsed
                elif isinstance(parsed, dict):
                    raw_flashcards = next((v for v in parsed.values() if isinstance(v, list)), [])
                else:
                    return []
                
                # Validação Estrutural com Pydantic
                valid_cards = []
                for card in raw_flashcards:
                    try:
                        valid_card = FlashcardSchema.model_validate(card)
                        valid_cards.append({"pergunta": valid_card.pergunta, "resposta": valid_card.resposta})
                    except ValidationError:
                        continue # Ignora card mal formatado e salva o resto
                
                return valid_cards
                
            except json.JSONDecodeError:
                print("Erro ao decodificar JSON gerado pelo modelo.")
                return []
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "rate" in error_msg or "quota" in error_msg:
                    if attempt < max_retries - 1:
                        wait = 30 * (attempt + 1)
                        print(f"Rate limit, aguardando {wait}s...")
                        time.sleep(wait)
                        continue
                
                print(f"Erro na API Groq no chunk atual: {e}. Pulando este chunk.")
                return [] # Retorna vazio em vez de quebrar a aplicação (isolamento de exceção)
        return []
