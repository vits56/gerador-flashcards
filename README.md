# Gerador de Flashcards Anki com IA 🧠⚡

O **Gerador de Flashcards Anki** é uma ferramenta de desktop para estudantes e concurseiros. Ele usa a inteligência artificial do **Groq (modelo Llama 3.3 70B)** para ler seus PDFs ou textos e gerar automaticamente dezenas de flashcards formatados para o **Anki** (`.apkg`).

> **A API do Groq possui um plano gratuito generoso**, sem necessidade de cartão de crédito.

---

## ⬇️ Download Rápido (Windows — Sem Instalação)

> **A forma mais fácil de usar o app!** Basta baixar e dar duplo clique.

1. Acesse a seção **[Releases](../../releases/latest)** deste repositório (botão no menu lateral direito do GitHub, ou clique no link).
2. Baixe o arquivo **`GeradorFlashcardsAnki.exe`** da versão mais recente.
3. Salve em qualquer pasta do seu computador (ex: Área de Trabalho).
4. Dê **duplo clique** no `.exe` para abrir o aplicativo. ✅

> ⚠️ **Aviso do Windows Defender:** É normal aparecer um alerta de "aplicativo desconhecido" porque o executável não tem assinatura digital paga. Para prosseguir, clique em **"Mais informações" → "Executar assim mesmo"**.

> 📁 **Onde ficam os flashcards gerados?** Os arquivos `.apkg` e o relatório `.txt` são salvos **automaticamente na sua pasta Downloads** (`C:\Users\SeuNome\Downloads`). Você não precisa procurar em nenhum outro lugar!


- 📄 **Leitura Inteligente de PDFs** — Extrai o texto do material de estudo, filtrando cabeçalhos e numerações de página.
- 📝 **Modo Texto Livre** — Cole trechos de resumos, anotações ou leis para gerar flashcards instantaneamente.
- 🤖 **IA Especializada em Concursos (Groq/Llama 3.3 70B)** — Analisa o texto em blocos e extrai regras, exceções, prazos, definições e pegadinhas de prova.
- 🛡️ **Validação com Pydantic** — Garante que a resposta da IA sempre respeite o formato Pergunta/Resposta. Cards mal gerados são ignorados silenciosamente.
- 💾 **Exportação nativa `.apkg`** — Pronto para importar no Anki com 1 clique.
- ⚙️ **Fail-Safe** — Erros em um bloco de texto nunca interrompem o processamento do restante.
- 🔐 **Chave salva localmente** — Você insere a chave uma única vez; o app a salva em `config.json` para as próximas sessões.

---

## 📋 Pré-requisitos

Antes de começar, você precisará ter instalado na sua máquina:

| Ferramenta | Versão mínima | Download |
|---|---|---|
| **Python** | 3.10+ | [python.org/downloads](https://www.python.org/downloads/) |
| **Anki** | Qualquer versão recente | [apps.ankiweb.net](https://apps.ankiweb.net/) |
| **Git** | Qualquer versão | [git-scm.com](https://git-scm.com/) |

> **Importante (Windows):** Durante a instalação do Python, marque a opção **"Add Python to PATH"** antes de clicar em *Install Now*.

---

## 🔑 Passo 1 — Obter sua Chave da API do Groq (Gratuito)

1. Acesse [console.groq.com](https://console.groq.com) e crie uma conta gratuita.
2. No painel, clique em **"API Keys"** no menu lateral.
3. Clique em **"Create API Key"**, dê um nome qualquer (ex: `flashcard-app`) e confirme.
4. **Copie a chave gerada** — ela começa com `gsk_`. Guarde-a em um lugar seguro pois ela só é exibida uma vez.

---

## 🚀 Passo 2 — Baixar e Instalar o Aplicativo

### Opção A: Executável (mais simples, Windows)

Se o repositório disponibilizar um arquivo `.exe` na seção **Releases**:

1. Acesse a aba [**Releases**](../../releases) deste repositório.
2. Baixe o arquivo `GeradorFlashcardsAnki.exe` da versão mais recente.
3. Salve-o em qualquer pasta (ex: Área de Trabalho).
4. Clique duas vezes no `.exe` para abrir o aplicativo. **Nenhuma instalação adicional é necessária.**
5. Os flashcards gerados serão salvos automaticamente em **`C:\Users\SeuNome\Downloads`**.

> Se o Windows Defender exibir um aviso de "aplicativo desconhecido", clique em **"Mais informações" → "Executar assim mesmo"**. Isso ocorre porque o executável não possui assinatura digital paga.

---

### Opção B: Rodar pelo Código-Fonte (Python)

Esta opção funciona em Windows, macOS e Linux.

#### 1. Clone o repositório

Abra o Terminal (PowerShell no Windows, Terminal no macOS/Linux) e execute:

```bash
git clone https://github.com/SEU_USUARIO/gerador-flashcards.git
cd gerador-flashcards
```

> **Sem Git?** Clique no botão verde **"Code"** nesta página → **"Download ZIP"**, extraia o arquivo e abra o terminal dentro da pasta extraída.

#### 2. Crie um Ambiente Virtual

O ambiente virtual isola as dependências do projeto sem afetar seu Python global.

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Após ativar, você verá `(.venv)` no início da linha do terminal. Isso confirma que o ambiente está ativo.

#### 3. Instale as Dependências

Com o ambiente virtual ativo, execute:

```bash
pip install -r requirements.txt
```

Aguarde o download e a instalação de todos os pacotes. Isso pode levar alguns minutos na primeira vez.

#### 4. Execute o Aplicativo

```bash
python main.py
```

A janela do aplicativo será aberta.

---

## 🖥️ Passo 3 — Usar o Aplicativo

### Tela Principal

Ao abrir o app, você verá duas abas na parte superior:

- **Arquivo PDF** — Para processar um documento PDF completo.
- **Texto Livre** — Para colar um trecho de texto, lei ou resumo diretamente.

### Inserindo a Chave da API

1. Cole sua chave Groq (começa com `gsk_`) no campo **"Cole sua Groq API Key aqui"** na parte inferior da janela.
2. A chave é salva automaticamente no arquivo `config.json` na mesma pasta do programa após o primeiro uso. **Nas próximas vezes que abrir o app, o campo já estará preenchido.**

### Gerando Flashcards a partir de um PDF

1. Clique na aba **"Arquivo PDF"**.
2. Clique em **"Selecionar PDF"** e escolha o arquivo desejado.
3. Verifique que o nome do arquivo apareceu abaixo do botão.
4. Clique no botão verde **"Gerar Flashcards"**.
5. Acompanhe o progresso na barra e no log de status na parte inferior.
6. Quando concluído, uma janela de sucesso aparecerá com o total de flashcards gerados.

### Gerando Flashcards a partir de Texto

1. Clique na aba **"Texto Livre"**.
2. (Opcional) Preencha o campo **"Título do Baralho"** — este será o nome do baralho no Anki.
3. Apague o texto de exemplo e cole o seu conteúdo na caixa de texto.
4. Clique em **"Gerar Flashcards"**.

---

## 📦 Passo 4 — Importar no Anki

Após a geração, dois arquivos serão criados na mesma pasta do programa:

| Arquivo | Descrição |
|---|---|
| `NomeDoArquivo_Flashcards.apkg` | O baralho pronto para importar no Anki |
| `NomeDoArquivo_Relatorio.txt` | Relatório com todos os flashcards em texto, para revisão |

**Para importar no Anki:**

1. Abra o **Anki** no seu computador.
2. Clique duas vezes no arquivo `.apkg` gerado **OU** vá em **Arquivo → Importar** dentro do Anki e selecione o arquivo.
3. O baralho aparecerá automaticamente na sua lista de decks, pronto para estudar!

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Função |
|---|---|
| **Python 3** | Linguagem base |
| **CustomTkinter** | Interface gráfica moderna com Dark Mode |
| **PyMuPDF (fitz)** | Extração de texto de PDFs |
| **Groq API** | Motor de LLM (Llama 3.3 70B) |
| **Pydantic** | Validação estrita do JSON gerado pela IA |
| **GenAnki** | Criação dos pacotes `.apkg` para o Anki |
| **Pytest** | Testes automatizados |
| **PyInstaller** | Empacotamento em executável `.exe` |

---

## ❓ Perguntas Frequentes (FAQ)

**O aplicativo trava ao processar PDFs grandes?**
> Não. O processamento roda em uma thread separada da interface gráfica. A janela permanece responsiva durante todo o processo.

**Meu PDF foi gerado por escaneamento (imagem). Funciona?**
> Não diretamente. O app extrai texto de PDFs digitais. Para PDFs escaneados, você precisará primeiro aplicar um OCR (como o Adobe Acrobat ou ferramentas gratuitas online) para converter a imagem em texto.

**Recebi um erro "Rate Limit" no log. O que fazer?**
> O plano gratuito do Groq tem limites de requisições por minuto. O app já tenta automaticamente até 4 vezes com espera crescente. Se persistir, aguarde alguns minutos e tente novamente.

**Onde fica o arquivo `.apkg` gerado?**
> Na mesma pasta onde o `main.py` ou o `.exe` está localizado.

**A chave `gsk_...` é segura?**
> Ela é salva apenas no arquivo `config.json` local na sua máquina. O arquivo está listado no `.gitignore` para **nunca ser enviado ao GitHub** acidentalmente.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma *issue* reportando bugs ou sugestões, ou enviar um *pull request* com melhorias.

---

## 📄 Licença

Este projeto está sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.
