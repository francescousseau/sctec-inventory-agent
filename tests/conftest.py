import pytest

from agente_estoque.config import Settings
from agente_estoque.estoque_tool import ProdutoEstoque


@pytest.fixture
def settings() -> Settings:
    # _env_file=None: testes nunca leem o .env real do aluno
    return Settings(
        _env_file=None,
        estoque_api_url="http://api.teste",
        estoque_retries=1,
        estoque_retry_backoff_s=0,
        mensagem_max_chars=200,
    )


def produto(codigo="PRD-001", nome="Mouse sem fio", q=5, m=10, un="un", cat="Periféricos") -> ProdutoEstoque:
    return ProdutoEstoque(
        codigo=codigo, nome=nome, categoria=cat, quantidade_atual=q, estoque_minimo=m, unidade=un
    )
