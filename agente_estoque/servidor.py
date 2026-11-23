"""Interface HTTP mínima que executa o MESMO grafo (usada pelo n8n).

    POST /analisar  {"mensagem": "..."}  ->  resposta do agente
    GET  /health

Execução:  uvicorn --factory agente_estoque.servidor:criar_app --port 8001
(a API do professor usa a porta 8000).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from agente_estoque import __version__
from agente_estoque.agente import criar_agente, executar


class Solicitacao(BaseModel):
    # limite alto só para proteger o servidor; o limite de negócio é validado no grafo
    mensagem: str = Field(max_length=5000, description="Pergunta em linguagem natural sobre estoque.")


class Analise(BaseModel):
    resposta: str
    desfecho: str
    intencao: str | None = None
    codigo: str | None = None
    situacao: str | None = None
    produto: dict[str, Any] | None = None
    api_consultada: bool = False
    caminho: list[str] = []
    erro: dict[str, str] | None = None


def criar_app(grafo=None) -> FastAPI:
    app = FastAPI(title="Agente de Estoque", version=__version__)
    app.state.grafo = grafo if grafo is not None else criar_agente()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "agente-estoque", "version": __version__}

    @app.post("/analisar", response_model=Analise)
    def analisar(corpo: Solicitacao) -> Analise:
        estado = executar(app.state.grafo, corpo.mensagem)
        return Analise(
            resposta=estado["resposta"],
            desfecho=estado["desfecho"],
            intencao=estado.get("intencao"),
            codigo=estado.get("codigo"),
            situacao=estado.get("situacao"),
            produto=estado.get("produto"),
            api_consultada=estado.get("api_consultada", False),
            caminho=estado.get("caminho", []),
            erro=estado.get("erro"),
        )

    return app
