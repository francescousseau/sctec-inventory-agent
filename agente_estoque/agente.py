"""Montagem do agente e execução com limites de segurança."""

from __future__ import annotations

import logging

from agente_estoque.config import Settings, get_settings
from agente_estoque.estado import EstadoAgente
from agente_estoque.estoque_tool import buscar_produto
from agente_estoque.grafo import Consulta, construir_grafo
from agente_estoque.interpretacao import Interpretador, criar_interpretador_llm

log = logging.getLogger("agente_estoque")

RECURSION_LIMIT = 12  # o grafo tem no máx. 5 nós por caminho; o limite é uma rede de segurança


def criar_agente(
    settings: Settings | None = None,
    interpretador: Interpretador | None = None,
    consulta: Consulta | None = None,
):
    """Cria o grafo com o LLM real (padrão). Parâmetros opcionais servem para testes."""
    settings = settings or get_settings()
    interpretador = interpretador or criar_interpretador_llm(settings)
    consulta = consulta or (lambda codigo: buscar_produto(codigo, settings))
    return construir_grafo(interpretador, consulta, settings)


def executar(grafo, mensagem: str) -> EstadoAgente:
    estado = grafo.invoke(
        {"mensagem": mensagem, "caminho": [], "api_consultada": False},
        config={"recursion_limit": RECURSION_LIMIT},
    )
    log.info(
        "desfecho=%s codigo=%s api=%s caminho=%s",
        estado.get("desfecho"), estado.get("codigo"), estado.get("api_consultada"),
        "→".join(estado.get("caminho", [])),
    )
    return estado
