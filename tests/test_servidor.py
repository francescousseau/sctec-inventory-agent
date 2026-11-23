from fastapi.testclient import TestClient

from agente_estoque.grafo import construir_grafo
from agente_estoque.servidor import criar_app
from agente_estoque.simulado import interpretador_simulado
from tests.conftest import produto


def cliente(settings):
    g = construir_grafo(interpretador_simulado, lambda c: produto(codigo=c), settings)
    return TestClient(criar_app(g))


def test_health(settings):
    assert cliente(settings).get("/health").json()["status"] == "ok"


def test_analisar_executa_o_mesmo_grafo(settings):
    r = cliente(settings).post("/analisar", json={"mensagem": "estoque do PRD-001"})
    assert r.status_code == 200
    j = r.json()
    assert j["situacao"] == "baixo" and j["api_consultada"] is True
    assert j["caminho"][-1] == "resposta_produto" and "ESTOQUE BAIXO" in j["resposta"]


def test_fora_de_escopo_via_http(settings):
    j = cliente(settings).post("/analisar", json={"mensagem": "qual a capital da França?"}).json()
    assert j["desfecho"] == "fora_de_escopo" and j["api_consultada"] is False


def test_corpo_malformado_e_422(settings):
    assert cliente(settings).post("/analisar", json={"texto": "x"}).status_code == 422
