"""
Serviço de IA para geração de diagramas YAML a partir de descrições textuais.
"""
from openai import OpenAI
from config.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL


def generate_yaml_from_prompt(prompt: str) -> str:
    """
    Gera um diagrama YAML a partir de uma descrição textual via OpenRouter.

    Args:
        prompt: Descrição do diagrama desejado

    Returns:
        YAML gerado como string
    """
    complete_prompt = _build_yaml_generation_prompt(prompt)
    yaml_response = _send_request(complete_prompt)
    return _clean_yaml_response(yaml_response)


def _send_request(prompt: str) -> str:
    try:
        client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente especializado em gerar diagramas YAML estruturados.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Erro ao comunicar com o serviço de IA: {str(e)}")


def _build_yaml_generation_prompt(user_prompt: str) -> str:
    return f"""
Crie um arquivo YAML para gerar um diagrama baseado na seguinte descrição:

{user_prompt}

O YAML deve seguir EXATAMENTE este formato em português brasileiro:

```yaml
diagrama:
  tipo: [casos de uso | classes | sequencia | componentes | implantacao | arquitetura]
  titulo: [Título descritivo do diagrama]
  descricao_alternativa: [Descrição acessível do diagrama]

  # Para tipo "arquitetura":
  usuarios:
    - nome: [nome do ator/usuário]
  servicos:
    - nome: [nome do serviço]
  conexoes:
    - de: [origem]
      para: [destino]
      evento: [descrição do fluxo]

  # Para tipo "classes":
  classes:
    - nome: [NomeDaClasse]
      atributos: [- tipo nome]
      metodos: [- tipo nome()]
  relacionamentos:
    - de: [Classe A]
      para: [Classe B]
      tipo: [herança | associação | dependência]

  # Para tipo "casos de uso":
  atores:
    - nome: [nome do ator]
  casos_de_uso:
    - nome: [nome do caso de uso]
  relacionamentos:
    - de: [origem]
      para: [destino]
      tipo: [associação | include | extend]

  # Para tipo "sequencia":
  objetos:
    - nome: [nome do objeto/componente]
  mensagens:
    - de: [origem]
      para: [destino]
      mensagem: [texto da mensagem]

  # Para tipo "componentes":
  componentes:
    - nome: [nome do componente]
  conexoes:
    - de: [origem]
      para: [destino]
      evento: [descrição]

  # Para tipo "implantacao":
  nos:
    - nome: [nome do nó]
  conexoes:
    - de: [origem]
      para: [destino]
      evento: [protocolo/descrição]
```

Escolha o tipo mais adequado para a descrição. Retorne APENAS o YAML, sem explicações.
Independente do idioma do prompt, o YAML deve ser sempre em português brasileiro.
"""


def _clean_yaml_response(yaml_response: str) -> str:
    return yaml_response.replace("```yaml", "").replace("```", "").strip()
