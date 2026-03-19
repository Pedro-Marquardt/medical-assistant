# Documentação Arquitetural: Assistente Virtual Médico

Esta documentação detalha as decisões de arquitetura e otimização para a Fase 3 do Tech Challenge, focando em performance, escalabilidade e compatibilidade de hardware da equipe.

## 1. Arquitetura da Aplicação

O sistema foi desenhado utilizando o **LangGraph** para orquestrar um fluxo de decisão inteligente e paralelo, separando regras de negócios de dados dinâmicos dos pacientes. A arquitetura é composta por:

* **Nó de Entrada & Roteamento Semântico:** Avalia a intenção da pergunta do usuário (query) para decidir o caminho de execução.
* **Vector DB (RAG):** Banco de dados vetorial dedicado exclusivamente a armazenar e consultar os **Protocolos Internos do Hospital**. Garante a explicabilidade (*explainability*) das condutas médicas indicadas.
* **Servidor MCP (Model Context Protocol):** Interface dedicada a consultar a base de dados estruturada (ex: SQLite/JSON) contendo as informações atualizadas e restrições dos **pacientes**.
* **Execução Paralela:** Quando a intenção exige, o sistema dispara requisições simultâneas para o Vector DB e para o Servidor MCP, unindo os retornos em um Contexto unificado.
* **LLM Customizada (Fine-Tuned):** O modelo processa o prompt final (regras de segurança + contexto RAG + contexto MCP) para gerar a resposta clínica validada.

---

## 2. O Código Universal para PyTorch

Para garantir que a aplicação rode nativamente no hardware de todos os membros da equipe (Apple Silicon, NVIDIA ou CPU) sem necessidade de alterar o código a cada commit, implementamos o roteamento dinâmico de tensores no PyTorch.

```python
import torch
from transformers import AutoModelForCausalLM

def get_optimal_device():
    """Detecta e retorna o melhor hardware acelerador disponível na máquina."""
    if torch.cuda.is_available():
        print("Hardware detectado: NVIDIA GPU (CUDA)")
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        print("Hardware detectado: Apple Silicon GPU (MPS)")
        return torch.device("mps")
    else:
        print("Hardware detectado: CPU (Modo de fallback)")
        return torch.device("cpu")

device = get_optimal_device()

# Exemplo de carregamento universal:
# modelo = AutoModelForCausalLM.from_pretrained("caminho").to(device)
```

---

## 3. Roteamento Semântico (Semantic Routing) no LangGraph

Em vez de depender de condicionais frágeis com palavras-chave (ex: `if "paciente" in query`), o LangGraph utiliza **Semantic Routing**. O sistema calcula a distância matemática (Similaridade do Cosseno) entre a pergunta do usuário e um cache vetorial de "âncoras de intenção".

* **Vantagem:** Evita acionamentos desnecessários ao Servidor MCP quando o médico faz uma pergunta clínica geral, economizando processamento.
* **Desempenho:** Utiliza um modelo de embeddings ultraleve rodando localmente para garantir o roteamento em tempo real (milissegundos).

### ⚠️ Nota Importante sobre a Inicialização das Âncoras

Para garantir que o tempo de resposta da API permaneça na casa dos milissegundos, **o cálculo vetorial das frases âncora NUNCA ocorre durante a requisição do usuário.** As âncoras de intenção são tokenizadas e vetorizadas **antes** da inicialização da API ou carregadas em memória global apenas uma vez no momento do *startup* do servidor. 

**Abordagem adotada (Em Memória no Startup):**
```python
from langchain_huggingface import HuggingFaceEmbeddings

# Inicializado globalmente no startup do servidor:
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
frases_ancora = ["estado do paciente", "ver prontuário", "exames pendentes"]

# Cache calculado uma única vez:
VETORES_ANCORA_CACHE = embeddings_model.embed_documents(frases_ancora)

# O Nó do LangGraph apenas processa a nova query:
def roteador_semantico(estado):
    vetor_usuario = embeddings_model.embed_query(estado["pergunta"])
    # Aplica a similaridade do cosseno comparando vetor_usuario e VETORES_ANCORA_CACHE
```
A API, durante o fluxo de execução, apenas vetoriza a *query* de entrada e realiza a comparação matemática contra a base já embutida na memória.