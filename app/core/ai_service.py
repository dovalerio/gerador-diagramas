"""
Serviço de IA para geração de diagramas YAML a partir de descrições textuais.
"""
import logging
from openai import OpenAI, RateLimitError, NotFoundError, APIStatusError
from config.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL, OPENROUTER_FALLBACK_MODELS

log = logging.getLogger(__name__)


def generate_yaml_from_prompt(
    prompt: str,
    model: str | None = None,
    fallback_models: list[str] | None = None,
) -> tuple[str, str]:
    # use env-configured fallbacks when caller doesn't specify any
    """
    Gera um diagrama YAML a partir de uma descrição textual via OpenRouter.

    Tenta `model` primeiro (ou OPENROUTER_MODEL se omitido), depois cada
    entrada de `fallback_models` em ordem, parando no primeiro sucesso.

    Returns:
        (yaml_content, model_used)
    """
    primary = model or OPENROUTER_MODEL
    effective_fallbacks = fallback_models if fallback_models is not None else OPENROUTER_FALLBACK_MODELS
    candidates = [primary] + list(effective_fallbacks)
    complete_prompt = _build_yaml_generation_prompt(prompt)
    last_exc: Exception | None = None

    for candidate in candidates:
        try:
            log.info("Tentando modelo: %s", candidate)
            raw = _send_request(complete_prompt, candidate)
            return _clean_yaml_response(raw), candidate
        except (RateLimitError, NotFoundError) as e:
            log.warning("Modelo %s indisponível (%s), tentando próximo...", candidate, type(e).__name__)
            last_exc = e
        except APIStatusError as e:
            if e.status_code == 402:
                log.warning("Modelo %s recusado por limite de gasto (402), tentando próximo...", candidate)
                last_exc = e
            else:
                raise
        # other exceptions propagate immediately

    raise last_exc


def _send_request(prompt: str, model: str) -> str:
    try:
        client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )
        response = client.chat.completions.create(
            model=model,
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
    except RateLimitError as e:
        log.warning("Rate limit no modelo %s: %s", model, e)
        raise
    except NotFoundError as e:
        log.error("Modelo não encontrado no OpenRouter (%s): %s", model, e)
        raise
    except Exception as e:
        log.exception("Erro ao comunicar com o serviço de IA (modelo: %s)", model)
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
