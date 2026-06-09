# Gerador de Flashcards Anki com IA 🧠⚡

O **Gerador de Flashcards Anki** é uma ferramenta de desktop projetada para estudantes, concurseiros e qualquer pessoa que deseje acelerar a criação de material de estudo. Ele utiliza a inteligência artificial avançada do **Groq (modelo Llama 3.3 70B)** para ler seus PDFs ou resumos em texto e gerar automaticamente dezenas de flashcards de alto nível formatados diretamente para o **Anki** (`.apkg`).

---

## 🌟 Funcionalidades

- 📄 **Leitura Inteligente de PDFs**: Extrai o texto do seu material de estudo, filtrando cabeçalhos e numerações de página desnecessárias.
- 📝 **Modo Texto Livre**: Permite colar trechos específicos de resumos, anotações de aula ou leis para gerar flashcards rápidos.
- 🤖 **Processamento Exaustivo com IA (Groq)**: Analisa o texto em blocos e extrai regras gerais, exceções, prazos, definições teóricas, competências e pegadinhas de prova. O modelo instruído age como um professor especialista em concursos públicos.
- 🛡️ **Validação Estrutural (Pydantic)**: O sistema à prova de falhas garante que as respostas da inteligência artificial sempre respeitem o formato Pergunta/Resposta. Se a IA "alucinar", o aplicativo ignora a falha e protege a exportação.
- 💾 **Exportação Nativa Anki (.apkg)**: Os cartões são gerados diretamente no formato nativo do Anki, prontos para importação com 1 clique (com formatação visual limpa e elegante).
- ⚙️ **Recuperação de Desastres (Fail-Safe)**: Se houver problemas de rede no meio de um PDF enorme, o aplicativo avisa sobre o erro no log, ignora a parte corrompida e salva todo o trabalho já processado.
- 🔐 **Persistência Segura**: Sua chave da API é salva localmente e automaticamente após o primeiro uso. Você não precisa colá-la novamente toda vez que abrir o aplicativo.

---

## 🚀 Como Funciona?

O aplicativo foi desenhado para ser simples e não travar o seu computador. Toda a interface gráfica e o processamento de IA rodam em processos (threads) separados.

1. **Seleção da Aba**: Escolha se quer upar um arquivo `.pdf` ou digitar um `Texto Livre`.
2. **Chave da API**: Insira sua [Groq API Key](https://console.groq.com/keys) (gratuita) no campo inferior. O app salvará automaticamente para os próximos usos.
3. **Chunking**: O programa "fatia" seu PDF em vários blocos de 3000 caracteres, respeitando o fim das frases (pontuação) para não cortar o raciocínio da inteligência artificial.
4. **Extração de Conhecimento**: O modelo `llama-3.3-70b-versatile` avalia cada bloco individualmente, retornando um JSON limpo e validado contendo perguntas e respostas vitais para provas.
5. **Empacotamento**: A biblioteca `genanki` empacota todos os cartões gerados junto com CSS elegante em um arquivo final `.apkg`.

---

## 📦 Como Usar

### Importando no Anki
1. Abra o aplicativo, carregue seu PDF e clique em **Gerar Flashcards**.
2. Quando concluído, o aplicativo avisará com um Popup de sucesso.
3. Vá até a pasta onde o programa está rodando. Você verá um arquivo chamado `Flashcards_Gerados.apkg` (ou o nome que você definiu).
4. Abra o **Anki** no seu computador e clique duas vezes no arquivo `.apkg` gerado para importá-lo.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3**
- **CustomTkinter**: Interface Gráfica moderna e Dark Mode.
- **PyMuPDF (fitz)**: Extração rápida e precisa de texto de PDFs.
- **Groq API**: Motor de LLM de altíssima velocidade.
- **Pydantic**: Validação estrita de tipagem (Model Validation) do JSON gerado pela IA.
- **GenAnki**: Criação programática de pacotes nativos para Anki.
- **Pytest**: Suíte de testes automatizados garantindo 100% de estabilidade da lógica.
