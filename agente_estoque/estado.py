"""Estado compartilhado do grafo (tipado)."""

import operator
from typing import Annotated, Any, TypedDict


class EstadoAgente(TypedDict, total=False):
    mensagem: str                 # entrada do usuário (higienizada)
    intencao: str                 # consultar_estoque | esclarecer | fora_escopo | erro
    codigo: str | None            # código PRD-XXX validado
    motivo: str                   # justificativa curta da interpretação
    produto: dict[str, Any] | None  # dados retornados pela API
    situacao: str | None          # disponivel | baixo | esgotado
    erro: dict[str, str] | None   # {"tipo": ..., "mensagem": ...}
    api_consultada: bool          # True se a ferramenta chegou a ser acionada
    resposta: str                 # texto final ao usuário
    desfecho: str                 # consulta_concluida | esclarecimento | fora_de_escopo | erro
    caminho: Annotated[list[str], operator.add]  # nós percorridos (auditoria)
