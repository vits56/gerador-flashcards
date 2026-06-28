from groq import Groq
import json
import re
import time

from typing import List, Dict, Callable, Optional, Tuple
from pydantic import BaseModel, ValidationError


class FlashcardSchema(BaseModel):
    pergunta: str
    resposta: str


class BaseFlashcardEngine:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self._log = log_callback or print
        self.system_instruction = """Você é um assistente cirúrgico de extração de dados para flashcards de concursos públicos. 

REGRA DE OURO (ATERRAMENTO):
Você deve basear as perguntas e respostas ESTRITAMENTE e EXCLUSIVAMENTE no texto fornecido. É terminantemente PROIBIDO inventar dados, usar conhecimentos externos ou criar flashcards sobre assuntos que não estão claramente escritos no texto. Se o texto não contiver informações úteis para prova, retorne um JSON vazio: {"flashcards": []}.

REGRA DE EXCLUSÃO (O QUE IGNORAR):
1. IGNORE sumariamente exercícios, listas de questões de múltipla escolha e gabaritos. Se o texto contiver opções como "a)", "b)", "c)", não crie flashcards sobre essa parte.
2. IGNORE resumos que apenas repetem o que já foi dito.
3. IGNORE exemplos hipotéticos, motivações do autor e introduções históricas.

O QUE EXTRAIR (FOCO TOTAL):
Extraia apenas conceitos teóricos de alta incidência: prazos, competências exclusivas/privativas de órgãos, regras gerais, exceções importantes e trechos com palavras restritivas/permissivas (ex: 'vedado', 'salvo', 'poderá', 'deverá'). 

FORMATAÇÃO DA SAÍDA:
A "pergunta" deve ser direta e em linguagem de banca examinadora. 
A "resposta" não pode conter letras de alternativas de múltipla escolha e deve ser concisa (máximo de 2 a 3 linhas).
Se o texto citar uma [IMAGEM_X] e ela for essencial para a teoria, inclua essa exata tag na pergunta ou na resposta.

Responda EXCLUSIVAMENTE com um JSON válido neste exato formato, sem qualquer texto ou explicação antes ou depois:
{
  "flashcards": [
    {"pergunta": "...", "resposta": "..."}
  ]
}"""

    def _extract_json_from_text(self, text: str) -> list:
        """Extrai o JSON da resposta do modelo de forma robusta."""
        text = re.sub(r'```(?:json)?\s*', '', text).strip().rstrip('`').strip()

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "flashcards" in parsed:
                return parsed["flashcards"]
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                for v in parsed.values():
                    if isinstance(v, list):
                        return v
            return []
        except json.JSONDecodeError:
            pass

        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return []


class GroqFlashcardEngine(BaseFlashcardEngine):
    def __init__(
        self,
        api_key: str,
        model_name: str = "llama-3.3-70b-versatile",
        log_callback: Optional[Callable[[str], None]] = None
    ):
        super().__init__(log_callback)
        self.api_key = api_key
        self.model_name = model_name
        self.client = Groq(api_key=self.api_key)

    def generate_flashcards(self, text_chunk: str) -> Tuple[List[Dict[str, str]], int]:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.system_instruction},
                        {"role": "user", "content": "Analise o texto abaixo seguindo rigorosamente as regras do sistema. Filtre as enrolações e questões de prova, extraindo apenas os dados teóricos essenciais. Gere os flashcards correspondentes em JSON:\n\n" + text_chunk}
                    ],
                    temperature=0.3,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )

                output_text = response.choices[0].message.content or ""
                tokens_used = 0
                if hasattr(response, 'usage') and response.usage:
                    tokens_used = response.usage.total_tokens

                raw_flashcards = self._extract_json_from_text(output_text)

                if not raw_flashcards:
                    self._log("     ⚠️ Modelo não retornou flashcards válidos neste bloco.")
                    return [], tokens_used

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

                return valid_cards, tokens_used

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
                    # Tenta extrair o tempo de espera real da mensagem do Groq
                    # Ex: "Please try again in 33m56.448s"
                    wait = 30  # fallback
                    time_match = re.search(r'try again in (?:(\d+)m)?(\d+(?:\.\d+)?)s', error_str)
                    if time_match:
                        mins = int(time_match.group(1) or 0)
                        secs = int(float(time_match.group(2)))
                        wait = mins * 60 + secs + 5  # +5s margem de segurança
                    
                    self._log(f"     ⏳ Limite da API atingido. Aguardando {wait}s...")
                    for remaining in range(wait, 0, -10):
                        time.sleep(min(10, remaining))
                        self._log(f"        ... {remaining}s restantes")
                    continue

                self._log(f"     ❌ Erro na API Groq: {error_str}")
                return [], 0
        return [], 0


