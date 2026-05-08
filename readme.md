# Gerador de Diagramas

Aplicação web para geração de diagramas UML e de arquitetura a partir de descrições YAML, com suporte a geração automática via IA.

## Funcionalidades

- Geração de diagramas a partir de YAML escrito manualmente
- Geração de YAML via IA a partir de descrição em linguagem natural (português ou inglês)
- 6 tipos de diagramas suportados: Arquitetura, Classes, Casos de Uso, Sequência, Componentes, Implantação
- Download e cópia do diagrama gerado
- Descrições alternativas para acessibilidade
- Interface responsiva acessível via navegador

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) — recomendado
- Ou: Python 3.12+, [Graphviz](https://graphviz.org/download/) instalado no PATH
- Chave de API do [OpenRouter](https://openrouter.ai/keys) (gratuito, sem cartão de crédito)

---

## Execução com Docker (recomendado)

### 1. Clone o repositório

```bash
git clone https://github.com/dovalerio/gerador-diagramas.git
cd gerador-diagramas
```

### 2. Configure as variáveis de ambiente

```bash
cp app/.env.example app/.env
```

Edite `app/.env` e adicione sua chave:

```env
OPENROUTER_API_KEY=sua-chave-aqui
```

Obtenha sua chave gratuita em: https://openrouter.ai/keys

### 3. Suba o container

```bash
docker compose up -d
```

### 4. Acesse a aplicação

Abra: http://localhost:5000

### Gerenciamento do container

```bash
docker compose logs -f        # ver logs
docker compose stop           # parar
docker compose down           # remover container
```

---

## Execução manual (sem Docker)

### Pré-requisitos adicionais

Instale o Graphviz:

```bash
# macOS
brew install graphviz

# Linux (Debian/Ubuntu)
sudo apt-get install graphviz

# Windows — baixe em https://graphviz.org/download/ e adicione ao PATH
```

### Instalação

```bash
git clone https://github.com/dovalerio/gerador-diagramas.git
cd gerador-diagramas

python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.\.venv\Scripts\activate

pip install -r app/requirements.txt

cp app/.env.example app/.env
# Edite app/.env com sua OPENROUTER_API_KEY
```

### Execução

```bash
python app/app.py
```

Acesse: http://127.0.0.1:5000

---

## Como usar

### Geração com IA

1. Na área **"Gerar YAML com IA"**, descreva o diagrama em texto livre
   - Exemplo: *"Diagrama de arquitetura para um e-commerce com frontend, API Gateway e banco de dados"*
2. Clique em **"Gerar YAML com IA"**
3. Revise e edite o YAML gerado, se necessário
4. Clique em **"Gerar Diagrama"**

### Geração manual

1. Escreva ou cole o YAML diretamente na área **"Editar YAML"**
2. Clique em **"Gerar Diagrama"**
3. Use os botões **Baixar** ou **Copiar Imagem** para exportar

---

## Configuração do modelo de IA

Por padrão, o modelo usado é o **Llama 3.3 70B** (gratuito no OpenRouter). Você pode trocar pelo modelo de sua preferência editando o `.env`:

```env
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
```

Outros modelos gratuitos disponíveis no OpenRouter:

| Modelo | Variável |
|---|---|
| Llama 3.3 70B (padrão) | `meta-llama/llama-3.3-70b-instruct:free` |
| Mistral 7B | `mistralai/mistral-7b-instruct:free` |
| Qwen 2 7B | `qwen/qwen-2-7b-instruct:free` |
| DeepSeek R1 | `deepseek/deepseek-r1:free` |

---

## Exemplos de YAML

Os templates prontos estão na pasta `templates/`. Exemplo de diagrama de arquitetura:

```yaml
diagrama:
  tipo: arquitetura
  titulo: "Arquitetura E-commerce"
  descricao_alternativa: "Diagrama de arquitetura de um sistema de e-commerce"
  usuarios:
    - nome: Cliente
    - nome: Administrador
  servicos:
    - nome: Frontend
    - nome: API Gateway
    - nome: Serviço de Produtos
    - nome: Banco de Dados
  conexoes:
    - de: Cliente
      para: Frontend
      evento: HTTPS
    - de: Frontend
      para: API Gateway
      evento: REST
    - de: API Gateway
      para: Serviço de Produtos
      evento: gRPC
    - de: Serviço de Produtos
      para: Banco de Dados
      evento: SQL
```

Tipos disponíveis: `arquitetura` · `classes` · `casos de uso` · `sequencia` · `componentes` · `implantacao`

---

## Estrutura do projeto

```
gerador-diagramas/
├── Dockerfile
├── docker-compose.yml
├── readme.md
├── templates/               # YAMLs de exemplo por tipo de diagrama
└── app/
    ├── .env.example
    ├── app.py               # entry point
    ├── requirements.txt
    ├── api/
    │   └── routes.py        # endpoints Flask
    ├── config/
    │   └── settings.py
    ├── core/
    │   ├── ai_service.py    # integração OpenRouter
    │   ├── diagram_manager.py
    │   ├── language_utils.py
    │   └── diagram_generators/
    │       ├── architecture_diagram.py
    │       ├── class_diagram.py
    │       ├── component_diagram.py
    │       ├── deployment_diagram.py
    │       ├── sequence_diagram.py
    │       └── use_case_diagram.py
    ├── static/
    │   ├── script.js
    │   └── style.css
    ├── templates/
    │   └── index.html
    └── tests/
        ├── test_generators.py
        └── test_routes.py
```

---

## Testes

```bash
cd app
python -m pytest tests/ -v
```

---

## Solução de problemas

**IA indisponível:** verifique se `OPENROUTER_API_KEY` está definida no `app/.env`.

**"Graphviz não encontrado":** instale o Graphviz e certifique-se de que o binário `dot` está no PATH. Com Docker esse problema não ocorre.

**Porta 5000 em uso:**
```bash
docker compose up -d -e PORT=8080
# ou edite docker-compose.yml: ports: "8080:5000"
```

---

## Contribuição

Pull requests são bem-vindos. Para mudanças maiores, abra uma issue primeiro para discutir o que você gostaria de alterar.
