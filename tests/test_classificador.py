import pytest

from agente_estoque.classificador import DadosInvalidos, Situacao, classificar


@pytest.mark.parametrize(
    "q,m,esperado",
    [
        (0, 20, Situacao.ESGOTADO),       # PRD-004
        (0, 0, Situacao.ESGOTADO),        # zero vence mesmo com mínimo 0
        (5, 10, Situacao.BAIXO),          # PRD-001
        (30, 30, Situacao.BAIXO),         # fronteira: igual ao mínimo = baixo (PRD-005)
        (1, 1, Situacao.BAIXO),
        (31, 30, Situacao.DISPONIVEL),    # logo acima da fronteira
        (40, 15, Situacao.DISPONIVEL),    # PRD-002
        (3, 0, Situacao.DISPONIVEL),      # mínimo 0 e quantidade positiva
    ],
)
def test_regra_e_fronteiras(q, m, esperado):
    assert classificar(q, m) is esperado


@pytest.mark.parametrize(
    "q,m",
    [(None, 5), (5, None), (-1, 5), (5, -1), ("5", 5), (5.0, 5), (True, 5), (5, False)],
)
def test_dados_invalidos_nao_geram_classificacao(q, m):
    with pytest.raises(DadosInvalidos):
        classificar(q, m)
