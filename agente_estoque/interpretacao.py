"""Interpretação da solicitação pelo LLM + validação da saída antes de usá-la.

Fluxo: Gemini (saída estruturada) -> Interpretacao (pydantic) ->
validar_interpretacao (regras em Python). Só depois o resultado pode rotear o
grafo ou chamar a ferramenta.
"""

from __future__ import annotations

import re
from typing import Callable, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from agente_estoque.config import Settings
from agente_estoque.instrucoes import INSTRUCOES_SISTEMA, montar_prompt_usuario

Intencao = Literal["consultar_estoque", "esclarecer", "fora_escopo"]

# Código PRD-XXX isolado (não aceita PRD-0012 nem XPRD-001).
_CODIGO_NO_TEXTO = re.compile(r"(?<![A-Z0-9])PRD-[0-9]{3}(?![0-9])")
_CODIGO_EXATO = re.compile(r"PRD-[0-9]{3}")


class Interpretacao(BaseModel):
    model_config = ConfigDict(extra="ignore")

    intencao: Intencao
    codigo: str | None = None
    motivo: str = ""


Interpretador = Callable[[str], Interpretacao]


class ErroInterpretador(Exception):
    """Falha ao obter ou entender a saída do LLM."""

    def __init__(self, tipo: str, mensagem: str):
        super().__init__(mensagem)
        self.tipo = tipo


def tipo_erro_llm(exc: BaseException) -> str:
    """Classifica a falha do Gemini percorrendo a cadeia de exceções.

    Usa o código HTTP (`code`) do google-genai e o status no texto, para não
    depender das classes de erro de uma versão específica do langchain.
    """
    atual: BaseException | None = exc
    while atual is not None:
        codigo, texto = getattr(atual, "code", None), str(atual)
        # chave inválida no AI Studio volta como 400 INVALID_ARGUMENT / API_KEY_INVALID
        if codigo in (401, 403) or "API_KEY_INVALID" in texto or "API key not valid" in texto:
            return "llm_autenticacao"
        if codigo == 429 or "RESOURCE_EXHAUSTED" in texto:
            return "llm_cota_excedida"
        if codigo == 404:
            return "llm_modelo_indisponivel"
        atual = atual.__cause__ or atual.__context__
    return "llm_indisponivel"


def codigos_na_mensagem(mensagem: str) -> set[str]:
    return set(_CODIGO_NO_TEXTO.findall(mensagem.upper()))


def validar_interpretacao(bruta: Interpretacao, mensagem: str) -> Interpretacao:
    """Aplica regras determinísticas à saída do LLM.

    Só autoriza "consultar_estoque" quando o código (a) segue PRD-XXX,
    (b) aparece literalmente na mensagem do usuário e (c) é o único código.
    Caso contrário, rebaixa para "esclarecer" (nunca consulta às cegas).
    """
    if bruta.intencao != "consultar_estoque":
        return Interpretacao(intencao=bruta.intencao, codigo=None, motivo=bruta.motivo)

    presentes = codigos_na_mensagem(mensagem)
    if len(presentes) > 1:
        return Interpretacao(
            intencao="esclarecer", codigo=None, motivo="a mensagem contém mais de um código"
        )

    codigo = (bruta.codigo or "").strip().upper()
    if not _CODIGO_EXATO.fullmatch(codigo) or codigo not in presentes:
        return Interpretacao(
            intencao="esclarecer",
            codigo=None,
            motivo="código ausente, malformado ou não encontrado no texto do usuário",
        )
    return Interpretacao(intencao="consultar_estoque", codigo=codigo, motivo=bruta.motivo)


def criar_interpretador_llm(settings: Settings) -> Interpretador:
    """Cria o interpretador com o Gemini (Gemini Developer API / Google AI Studio)."""
    chave_configurada = (
        settings.google_api_key is not None
        and bool(settings.google_api_key.get_secret_value().strip())
    )
    if not chave_configurada:
        def interpretador_sem_configuracao(_mensagem: str) -> Interpretacao:
            raise ErroInterpretador(
                "configuracao_ausente", "GOOGLE_API_KEY não configurada (veja .env.example)."
            )
        return interpretador_sem_configuracao

    from langchain_core.exceptions import OutputParserException
    from langchain_google_genai import ChatGoogleGenerativeAI  # import tardio: testes não exigem o pacote

    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        timeout=settings.llm_timeout_s,
        temperature=0,
        max_retries=1,  # padrão é 6: com cota estourada só atrasaria o erro
    ).with_structured_output(Interpretacao)

    def interpretar(mensagem: str) -> Interpretacao:
        try:
            resultado = llm.invoke(
                [("system", INSTRUCOES_SISTEMA), ("human", montar_prompt_usuario(mensagem))]
            )
        except (OutputParserException, ValidationError) as exc:
            raise ErroInterpretador("saida_llm_invalida", "Saída do LLM fora do formato.") from exc
        except Exception as exc:  # rede, autenticação, cota...
            tipo = tipo_erro_llm(exc)
            mensagens = {
                "llm_autenticacao": "Gemini recusou a credencial (GOOGLE_API_KEY inválida ou sem permissão).",
                "llm_cota_excedida": "Cota/limite de requisições da Gemini API excedido.",
                "llm_modelo_indisponivel": f"Modelo {settings.gemini_model!r} indisponível (revise GEMINI_MODEL).",
                "llm_indisponivel": "Falha ao chamar o LLM.",
            }
            raise ErroInterpretador(tipo, mensagens[tipo]) from exc
        if not isinstance(resultado, Interpretacao):
            raise ErroInterpretador("saida_llm_invalida", "Saída do LLM fora do formato.")
        return resultado

    return interpretar
