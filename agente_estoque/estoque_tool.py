"""Ferramenta Python: consulta HTTP somente leitura à API de estoque.

Finalidade : obter UM produto pelo código (GET /produtos/{codigo}).
Parâmetro  : codigo (str) no formato PRD-XXX (três dígitos).
Retorno    : ProdutoEstoque (codigo, nome, categoria, quantidade_atual,
             estoque_minimo, unidade) já validado.
Falhas     : CodigoInvalido, ProdutoNaoEncontrado, ServicoIndisponivel,
             RespostaInvalida (todas herdam de ErroEstoque).

Restrições de segurança:
  * só faz GET e só em {ESTOQUE_API_URL}/produtos/{codigo};
  * o código é validado por regex ANTES de entrar na URL (sem path traversal);
  * sem redirecionamentos; timeout em toda chamada.
"""

from __future__ import annotations

import re
import time

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from agente_estoque.config import Settings, get_settings

_PADRAO_CODIGO = re.compile(r"PRD-[0-9]{3}")  # usado com fullmatch


class ErroEstoque(Exception):
    """Base das falhas previsíveis da ferramenta."""

    tipo = "erro_estoque"


class CodigoInvalido(ErroEstoque):
    tipo = "codigo_invalido"


class ProdutoNaoEncontrado(ErroEstoque):
    tipo = "produto_nao_encontrado"


class ServicoIndisponivel(ErroEstoque):
    tipo = "servico_indisponivel"


class RespostaInvalida(ErroEstoque):
    tipo = "resposta_invalida"


class ProdutoEstoque(BaseModel):
    """Estrutura esperada de um produto retornado pela API (tipos estritos)."""

    model_config = ConfigDict(strict=True, extra="ignore")

    codigo: str
    nome: str = Field(min_length=1)
    categoria: str = Field(min_length=1)
    quantidade_atual: int = Field(ge=0)
    estoque_minimo: int = Field(ge=0)
    unidade: str = Field(min_length=1)


def codigo_valido(codigo: object) -> bool:
    return isinstance(codigo, str) and _PADRAO_CODIGO.fullmatch(codigo) is not None


def buscar_produto(
    codigo: str,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
) -> ProdutoEstoque:
    """Consulta um produto na API de estoque. Ver docstring do módulo."""
    settings = settings or get_settings()
    if not codigo_valido(codigo):
        raise CodigoInvalido("Código fora do padrão PRD-XXX.")

    url = f"{settings.estoque_api_url}/produtos/{codigo}"
    resposta = _get_com_retentativa(url, settings, client)

    status = resposta.status_code
    if status == 200:
        return _validar_produto(resposta, codigo)
    if status == 404:
        raise ProdutoNaoEncontrado(f"Produto {codigo} não existe na API de estoque.")
    if status == 422:
        raise CodigoInvalido("A API rejeitou o código informado.")
    if status == 503 or 500 <= status < 600:
        raise ServicoIndisponivel(f"A API de estoque respondeu HTTP {status}.")
    raise RespostaInvalida(f"Status HTTP inesperado da API: {status}.")


def _get_com_retentativa(url: str, settings: Settings, client: httpx.Client | None) -> httpx.Response:
    tentativas = max(0, settings.estoque_retries) + 1
    ultimo_erro: Exception | None = None
    proprio = client is None
    cliente = client or httpx.Client(timeout=settings.estoque_timeout_s, follow_redirects=False)
    try:
        for n in range(tentativas):
            try:
                return cliente.get(url, timeout=settings.estoque_timeout_s)
            except httpx.TransportError as exc:  # timeout, conexão recusada, DNS...
                ultimo_erro = exc
                if n < tentativas - 1:
                    time.sleep(settings.estoque_retry_backoff_s * (n + 1))
    finally:
        if proprio:
            cliente.close()
    raise ServicoIndisponivel("Não foi possível contatar a API de estoque.") from ultimo_erro


def _validar_produto(resposta: httpx.Response, codigo_pedido: str) -> ProdutoEstoque:
    try:
        corpo = resposta.json()
        produto = ProdutoEstoque.model_validate(corpo)
    except (ValueError, ValidationError) as exc:
        raise RespostaInvalida("A API retornou um produto fora da estrutura esperada.") from exc
    if produto.codigo != codigo_pedido:
        raise RespostaInvalida("A API retornou um produto diferente do solicitado.")
    return produto
