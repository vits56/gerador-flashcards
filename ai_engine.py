from groq import Groq
import json
import re
import time
import urllib.request
import urllib.error
from typing import List, Dict, Callable, Optional
from pydantic import BaseModel, ValidationError


class FlashcardSchema(BaseModel):
    pergunta: str
    resposta: str


class BaseFlashcardEngine:
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self._log = log_callback or print
        self.system_instruction = """Você é um professor especialista na criação de flashcards de alto rendimento para provas de concursos públicos brasileiros.

Sua tarefa é analisar o texto fornecido e extrair APENAS as informações que têm alto potencial de cobrança em provas objetivas, ignorando qualquer conteúdo que seja apenas contexto, introdução ou enrolação.

Concentre-se em criar flashcards cirúrgicos sobre:
- Prazos, datas, quóruns, idades e penalidades (Literalidade da Lei).
- Regras gerais e, principalmente, suas EXCEÇÕES.
- Definições teóricas diretas e classificações importantes.
- Competências exclusivas e privativas de órgãos, autoridades ou entes.
- Palavras-chave restritivas (ex: "somente", "vedado", "prescindível").

REGRAS RIGOROSAS:
- Filtro de Relevância: IGNORE introduções históricas, exemplos longos, motivações do autor do texto ou conceitos óbvios.
- Atomicidade: Cada flashcard deve cobrar apenas UMA informação. A resposta deve ser curta, direta e ter no máximo 2 a 3 linhas.
- Imagens: Se o texto contiver marcações de imagens (ex: [IMAGEM_X]), avalie se ela é importante. Se for, insira a tag exatamente como está no texto na "pergunta" ou na "resposta" para que o sistema a exiba.

Responda EXCLUSIVAMENTE com um JSON válido neste exato formato, sem explicações antes ou depois:
{
  "flashcards": [
    {"pergunta": "...", "resposta": "..."},
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

    def generate_flashcards(self, text_chunk: str) -> List[Dict[str, str]]:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.system_instruction},
                        {"role": "user", "content": "Analise o texto abaixo, filtre a enrolação e crie flashcards concisos APENAS com os dados que seriam cobrados por uma banca examinadora rigorosa:\n\n" + text_chunk}
                    ],
                    temperature=0.3,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )

                output_text = response.choices[0].message.content or ""
                raw_flashcards = self._extract_json_from_text(output_text)

                if not raw_flashcards:
                    self._log("     ⚠️ Modelo não retornou flashcards válidos neste bloco.")
                    return []

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
                return []
        return []


class OllamaFlashcardEngine(BaseFlashcardEngine):
    def __init__(
        self,
        model_name: str = "llama3.1",
        log_callback: Optional[Callable[[str], None]] = None
    ):
        super().__init__(log_callback)
        self.model_name = model_name.replace("Ollama: ", "").strip()
        self.url = "http://127.0.0.1:11434/api/chat"

    def generate_flashcards(self, text_chunk: str) -> List[Dict[str, str]]:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": self.system_instruction},
                {"role": "user", "content": "Analise o texto abaixo, filtre a enrolação e crie flashcards concisos APENAS com os dados que seriam cobrados por uma banca examinadora rigorosa:\n\n" + text_chunk}
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_ctx": 4096
            }
        }
        
        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=1200) as response:
                result = json.loads(response.read().decode('utf-8'))
                output_text = result.get("message", {}).get("content", "")
                
                raw_flashcards = self._extract_json_from_text(output_text)
                
                if not raw_flashcards:
                    self._log("     ⚠️ Modelo local não retornou flashcards válidos neste bloco.")
                    return []
                    
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
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='ignore')
            self._log(f"     ❌ Erro do Ollama (Código {e.code}): {error_body}")
            return []
        except urllib.error.URLError as e:
            self._log(f"     ❌ Erro de conexão com o Ollama: {e.reason}. Verifique se o Ollama está rodando.")
            return []
        except Exception as e:
            self._log(f"     ❌ Erro desconhecido com Ollama: {str(e)}")
            return []
