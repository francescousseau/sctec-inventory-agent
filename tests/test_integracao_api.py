"""Integração com a API REAL do professor (precisa estar rodando).

  cd api-estoque && python -m uvicorn app.main:app --port 8000
  pytest -m integracao -v

Usa o interpretador SIMULADO (sem LLM): valida ferramenta + grafo + dados reais.
Os testes são ignorados automaticamente se a API estiver offline.
"""

import httpx
import pytest

from agente_estoque.agente import executar
from agente_estoque.config import Settings
from agente_estoque.estoque_tool import buscar_produto
from agente_estoque.grafo import construir_grafo
from agente_estoque.simulado import interpretador_simulado

pytestmark = pytest.mark.integracao
URL = Settings(_env_file=None).estoque_api_url


def _api_no_ar() -> bool:
    try:
        return httpx.get(f"{URL}/health", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


@pytest.fixture(scope="module")
def grafo():
    if not _api_no_ar():
        pytest.skip(f"API de estoque offline em {URL}")
    s = Settings(_env_file=None, estoque_api_url=URL)
    return construir_grafo(interpretador_simulado, lambda c: buscar_produto(c, s), s)


@pytest.mark.parametrize(
    "codigo,situacao",
    [("PRD-001", "baixo"), ("PRD-002", "disponivel"), ("PRD-004", "esgotado"),
     ("PRD-005", "baixo"), ("PRD-009", "baixo"), ("PRD-012", "disponivel")],
)
def test_situacao_confere_com_dados_da_api(grafo, codigo, situacao):
    bruto = httpx.get(f"{URL}/produtos/{codigo}").json()
    r = executar(grafo, f"Como está o estoque do {codigo}?")
    assert r["situacao"] == situacao
    assert r["produto"]["quantidade_atual"] == bruto["quantidade_atual"]
    assert r["produto"]["estoque_minimo"] == bruto["estoque_minimo"]


def test_produto_inexistente_real(grafo):
    r = executar(grafo, "estoque do PRD-999")
    assert r["erro"]["tipo"] == "produto_nao_encontrado" and r.get("situacao") is None


def test_503_real(grafo):
    r = executar(grafo, "estoque do PRD-503")
    assert r["erro"]["tipo"] == "servico_indisponivel" and r.get("situacao") is None


def test_api_offline_real():
    s = Settings(_env_file=None, estoque_api_url="http://127.0.0.1:9", estoque_retries=0, estoque_timeout_s=1)
    g = construir_grafo(interpretador_simulado, lambda c: buscar_produto(c, s), s)
    r = executar(g, "estoque do PRD-001")
    assert r["erro"]["tipo"] == "servico_indisponivel" and r.get("situacao") is None
