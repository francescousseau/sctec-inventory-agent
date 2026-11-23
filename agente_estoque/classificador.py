"""Classificação determinística do estoque (feita em Python, nunca pelo LLM).

Regra (confirmada no README da API do professor, seção 5):
    quantidade == 0               -> ESGOTADO
    0 < quantidade <= minimo      -> BAIXO        (igual ao mínimo CONTA como baixo)
    quantidade > minimo           -> DISPONIVEL

Fronteiras: quantidade == minimo (> 0) é BAIXO. Se quantidade == 0, é ESGOTADO
mesmo quando minimo == 0 (a verificação de zero vem primeiro).
Dados ausentes, negativos ou de tipo errado geram DadosInvalidos: nunca há
classificação presumida.
"""

from enum import Enum


class Situacao(str, Enum):
    DISPONIVEL = "disponivel"
    BAIXO = "baixo"
    ESGOTADO = "esgotado"


ROTULOS = {
    Situacao.DISPONIVEL: "DISPONÍVEL",
    Situacao.BAIXO: "ESTOQUE BAIXO",
    Situacao.ESGOTADO: "ESGOTADO",
}


class DadosInvalidos(ValueError):
    """Quantidade ou mínimo ausentes, não inteiros ou negativos."""


def _inteiro_nao_negativo(valor: object, nome: str) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        raise DadosInvalidos(f"{nome} inválido: {valor!r}")
    return valor


def classificar(quantidade: object, minimo: object) -> Situacao:
    q = _inteiro_nao_negativo(quantidade, "quantidade_atual")
    m = _inteiro_nao_negativo(minimo, "estoque_minimo")
    if q == 0:
        return Situacao.ESGOTADO
    if q <= m:
        return Situacao.BAIXO
    return Situacao.DISPONIVEL
