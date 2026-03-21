# 🏥 Assistente Médico Virtual - Tech Challenge (PoC)

Este repositório contém os artefatos da Prova de Conceito (PoC) para a criação de um assistente virtual focado em protocolos médicos. 

Durante o desenvolvimento deste projeto, realizamos o treinamento de um modelo de linguagem (LLM) próprio, aplicando *Fine-Tuning* (LoRA) sobre o modelo base Mistral 7B.

---

## 🏗️ Decisão Arquitetural: O uso do modelo treinado

Embora o *fine-tuning* tenha sido realizado e validado com sucesso, **optamos por não utilizar o modelo treinado na aplicação que utiliza os grafos deste projeto.**

**Por quê?**
Por questões de processamento e flexibilidade da arquitetura. Ao passar pelo *fine-tuning* focado estritamente no formato de instrução direta (Text-to-Text), o modelo tornou-se "pequeno" e excessivamente especializado. 

A nossa arquitetura final desejada exige capacidades avançadas de *Retrieval-Augmented Generation* (RAG) e *Tool Calling* para consultar sistemas e documentos dinâmicos do hospital em tempo real. Testes empíricos demonstraram que o modelo base puro possui maior "fôlego cognitivo" para ler grandes blocos de contexto injetados via RAG sem sofrer de vício de formato (*overfitting* de prompt). 

O modelo treinado foi mantido no projeto como um artefato de pesquisa e para demonstração da técnica de aprendizado de máquina.

---

## 📂 Estrutura do Projeto (Reprodutibilidade)

Todo o processo de treinamento e preparação dos dados foi rigorosamente documentado para a banca avaliadora e pode ser encontrado nas seguintes pastas:

* **`/data`**: Contém o dataset base utilizado para ensinar os protocolos médicos ao modelo.
* **`/jupyter`**: Contém os notebooks com o passo a passo completo do projeto de *Fine-Tuning* (limpeza de dados, configuração do Unsloth, treinamento LoRA, geração do modelo e testes locais).

---

## � Como rodar o projeto completo (API + ChromaDB)

Para executar a aplicação completa com todos os serviços necessários:

### Pré-requisitos
- Docker e Docker Compose instalados
- Porta 3030 (API) e 8000 (ChromaDB) disponíveis

### Executando o projeto

**1. Clone o repositório e navegue até a pasta raiz**
```bash
cd medical-assistant
```

**2. Construa e inicie todos os serviços**
```bash
docker-compose up -d
```

**3. Verifique se os serviços estão funcionando**
```bash
docker-compose ps
```

### Acessando a aplicação

- **API**: http://localhost:3030/
- **ChromaDB**: http://localhost:8000/
- **Health Check da API**: http://localhost:3030/health/chroma

### Comandos úteis

**Ver logs da API:**
```bash
docker-compose logs api
```

**Ver logs do ChromaDB:**
```bash
docker-compose logs chroma
```

**Ver logs do MCP Server:**
```bash
docker-compose logs mcp-server
```

**Parar os serviços:**
```bash
docker-compose down
```

**Rebuild completo após mudanças:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Arquitetura dos Serviços

1. **ChromaDB**: Banco de dados vetorial para protocolos médicos (RAG)
2. **API FastAPI**: Interface principal com injeção de dependências  
3. **MCP Server**: Servidor de dados de pacientes para consulta do LLM

O **MCP Server** expõe uma ferramenta chamada `get_patient_data` que permite ao LLM consultar dados de pacientes por CPF, com opções de filtro para alergias, doenças ou informações completas.

---

## �🚀 Como rodar o experimento treinado localmente

Caso deseje testar o modelo que foi treinado com os dados do hospital, ele foi exportado para o formato leve `.gguf` para rodar de forma otimizada via **Ollama** usando processamento de CPU/GPU unificada.

### ⚠️ Pré-requisito: Executar os Notebooks

**IMPORTANTE**: Para gerar o modelo `.gguf` exportado, você deve executar os notebooks do Jupyter na seguinte ordem:

1. **`dataset.ipynb`** - Preparação e limpeza dos dados
2. **`finetuning.ipynb`** - Treinamento do modelo com LoRA
3. **`export_gguf.ipynb`** - Exportação do modelo treinado para formato `.gguf`

Somente após executar todos os notebooks nesta sequência, o arquivo `mistral-7b-v0.3.Q4_K_M.gguf` estará disponível para uso com o Ollama.

### Passo a passo para usar o modelo exportado:

**1. Acesse a pasta dos modelos**
Pelo seu terminal, navegue até o diretório onde o arquivo `.gguf` exportado e o `Modelfile` estão salvos:
```bash
cd models
```

**2. Construa o modelo no Ollama**
Utilize o comando abaixo para que o Ollama leia a "receita" do Modelfile, importe os pesos do .gguf e crie a imagem do modelo no seu sistema. Vamos chamá-lo de `assistente_postech`:

```bash
ollama create assistente_postech -f Modelfile
```

(Aguarde até a mensagem de success aparecer no terminal).

**3. Teste o modelo no terminal**
Para interagir com o modelo treinado diretamente pela linha de comando, execute:
```bash
ollama run assistente_postech
```