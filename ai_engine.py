from groq import Groq
import json
import re
import time
from typing import List, Dict, Callable, Optional
from pydantic import BaseModel, ValidationError


class FlashcardSchema(BaseModel):
    pergunta: str
    resposta: str


class GroqFlashcardEngine:
    def __init__(
        self,
        api_key: str,
        model_name: str = "llama-3.3-70b-versatile",
        log_callback: Optional[Callable[[str], None]] = None
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.client = Groq(api_key=self.api_key)
        # Callback para exibir mensagens na UI (substitui print())
        self._log = log_callback or print

        self.system_instruction = """Você é um professor especialista na criação de flashcards para provas de concursos públicos brasileiros.
Sua tarefa é analisar o texto fornecido e extrair ABSOLUTAMENTE TODAS as informações que possam ser alvo de questões de prova.
Você deve criar dezenas de flashcards abrangentes cobrindo:
- Regras gerais e suas exceções.
- Prazos, datas e penalidades.
- Definições teóricas, classificações e conceitos.
- Competências de órgãos, autoridades ou entes.
- Qualquer detalhe mnemônico ou pegadinha comum em provas.

Seja exaustivo: não deixe nenhum detalhe de fora.

Responda EXCLUSIVAMENTE com um JSON válido neste formato, sem texto antes ou depois:
[
  {"pergunta": "...", "resposta": "..."}
]"""

    def _extract_json_from_text(self, text: str) -> list:
        """
        Extrai o JSON da resposta do modelo de forma robusta.
        Suporta resposta pura, dentro de ```json ... ```, ou objeto {flashcards: []}.
        """
        # Remove blocos de código markdown se existirem
        text = re.sub(r'```(?:json)?\s*', '', text).strip().rstrip('`').strip()

        # Tenta parsear diretamente
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                # Procura qualquer chave cujo valor seja uma lista
                for v in parsed.values():
                    if isinstance(v, list):
                        return v
            return []
        except json.JSONDecodeError:
            pass

        # Tenta encontrar um array JSON no texto (ex: texto antes/depois do JSON)
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return []

    def generate_flashcards(self, text_chunk: str) -> List[Dict[str, str]]:
        """
        Envia um bloco de texto ao Groq e retorna lista de {pergunta, resposta}.
        Erros são reportados via log_callback em vez de print() invisível.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.system_instruction},
                        {
                            "role": "user",
                            "content": (
                                "Crie flashcards para TODOS os detalhes "
                                "do seguinte texto:\n\n" + text_chunk
                            )
                        }
                    ],
                    temperature=0.3,
                    max_tokens=2048,
                    # Sem response_format — parseamos manualmente para maior compatibilidade
                )

                output_text = response.choices[0].message.content or ""
                raw_flashcards = self._extract_json_from_text(output_text)

                if not raw_flashcards:
                    self._log("     ⚠️ Modelo não retornou flashcards válidos neste bloco.")
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
                        continue

                return valid_cards

            except Exception as e:
                error_str = str(e)
                error_lower = error_str.lower()
                is_rate_limit = (
                    "429" in error_str
                    or "rate" in error_lower
                    or "quota" in error_lower
                    or "too many" in error_lower
                )

                if is_rate_limit and attempt < max_retries - 1:
                    wait = 60 * (attempt + 1)
                    self._log(f"     ⏳ Limite da API atingido. Aguardando {wait}s...")
                    for remaining in range(wait, 0, -5):
                        time.sleep(5)
                        self._log(f"        ... {remaining}s restantes")
                    continue

                # Erro real — mostra na UI em vez de sumir no print()
                self._log(f"     ❌ Erro na API Groq: {error_str}")
                return []

        return []
