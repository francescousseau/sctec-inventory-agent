import httpx
import pytest

from agente_estoque.estoque_tool import (
    CodigoInvalido,
    ProdutoNaoEncontrado,
    RespostaInvalida,
    ServicoIndisponivel,
    buscar_produto,
)

OK = {"codigo": "PRD-001", "nome": "Mouse sem fio", "categoria": "Periféricos",
      "quantidade_atual": 5, "estoque_minimo": 10, "unidade": "un"}


def cliente(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_sucesso_e_url_somente_leitura(settings):
    vistos = []

    def h(req):
        vistos.append((req.method, str(req.url)))
        return httpx.Response(200, json=OK)

    p = buscar_produto("PRD-001", settings, cliente(h))
    assert (p.codigo, p.quantidade_atual, p.estoque_minimo) == ("PRD-001", 5, 10)
    assert vistos == [("GET", "http://api.teste/produtos/PRD-001")]


@pytest.mark.parametrize("codigo", ["prd-001", "PRD-1", "PRD-0012", "ABC-001", "", "PRD-001\n",
                                    "../health", "PRD-001/../x", None, 123, "PRD-٠٠١"])
def test_codigo_invalido_nem_chega_na_rede(settings, codigo):
    def h(req):
        raise AssertionError("não deveria haver requisição")

    with pytest.raises(CodigoInvalido):
        buscar_produto(codigo, settings, cliente(h))


def test_404_produto_inexistente(settings):
    c = cliente(lambda r: httpx.Response(404, json={"erro": "produto_nao_encontrado", "mensagem": "x"}))
    with pytest.raises(ProdutoNaoEncontrado):
        buscar_produto("PRD-999", settings, c)


def test_503_servico_indisponivel_sem_retentativa(settings):
    chamadas = []

    def h(req):
        chamadas.append(1)
        return httpx.Response(503, json={"erro": "servico_indisponivel", "mensagem": "x"})

    with pytest.raises(ServicoIndisponivel):
        buscar_produto("PRD-503", settings, cliente(h))
    assert len(chamadas) == 1  # 503 não é retentado (retentativa só para falha de rede)


def test_500_vira_servico_indisponivel(settings):
    c = cliente(lambda r: httpx.Response(500, json={"erro": "erro_armazenamento", "mensagem": "x"}))
    with pytest.raises(ServicoIndisponivel):
        buscar_produto("PRD-001", settings, c)


def test_422_da_api(settings):
    c = cliente(lambda r: httpx.Response(422, json={"erro": "codigo_invalido"}))
    with pytest.raises(CodigoInvalido):
        buscar_produto("PRD-001", settings, c)


def test_falha_de_rede_retenta_e_depois_indisponivel(settings):
    n = []

    def h(req):
        n.append(1)
        raise httpx.ConnectError("recusada")

    with pytest.raises(ServicoIndisponivel):
        buscar_produto("PRD-001", settings, cliente(h))
    assert len(n) == settings.estoque_retries + 1


def test_timeout_vira_indisponivel(settings):
    def h(req):
        raise httpx.ReadTimeout("lento")

    with pytest.raises(ServicoIndisponivel):
        buscar_produto("PRD-001", settings, cliente(h))


def test_recupera_na_segunda_tentativa(settings):
    estado = {"n": 0}

    def h(req):
        estado["n"] += 1
        if estado["n"] == 1:
            raise httpx.ConnectError("blip")
        return httpx.Response(200, json=OK)

    assert buscar_produto("PRD-001", settings, cliente(h)).codigo == "PRD-001"


@pytest.mark.parametrize(
    "corpo",
    [
        {**OK, "quantidade_atual": "5"},        # tipo errado
        {**OK, "quantidade_atual": True},       # bool não é inteiro
        {**OK, "estoque_minimo": -1},           # negativo
        {k: v for k, v in OK.items() if k != "estoque_minimo"},  # campo ausente
        {**OK, "codigo": "PRD-002"},            # produto diferente do pedido
        ["lista", "em vez de objeto"],
    ],
)
def test_resposta_estruturalmente_invalida(settings, corpo):
    with pytest.raises(RespostaInvalida):
        buscar_produto("PRD-001", settings, cliente(lambda r: httpx.Response(200, json=corpo)))


def test_corpo_nao_json(settings):
    with pytest.raises(RespostaInvalida):
        buscar_produto("PRD-001", settings, cliente(lambda r: httpx.Response(200, text="<html>")))


def test_redirecionamento_nao_e_seguido(settings):
    c = cliente(lambda r: httpx.Response(302, headers={"location": "http://evil.example/"}))
    with pytest.raises(RespostaInvalida):
        buscar_produto("PRD-001", settings, c)
