"""Grafo LangGraph do agente.

                      ┌────────────────┐  entrada inválida
          START ────▶ │ validar_entrada│ ─────────────────────────────┐
                      └───────┬────────┘                              │
                              ▼                                       │
                      ┌────────────────┐  erro do LLM                 │
                      │   interpretar  │ ─────────────────────────────┤
                      │ (LLM+validação)│                              │
                      └───────┬────────┘                              │
        DECISÃO (aresta condicional #1)                               │
        ┌─────────────────────┼───────────────────────┐               │
        ▼ consultar_estoque   ▼ esclarecer            ▼ fora_escopo   ▼
 ┌─────────────────┐  ┌───────────────────┐  ┌──────────────────┐ ┌──────────────┐
 │consultar_estoque│  │resposta_esclareci-│  │resposta_fora_    │ │resposta_erro │
 │  (ferramenta)   │  │mento              │  │escopo            │ │              │
 └───────┬─────────┘  └─────────┬─────────┘  └────────┬─────────┘ └──────┬───────┘
  erro? ─┼─▶ resposta_erro      ▼                     ▼                  ▼
         ▼ ok                  END                   END                END
 ┌─────────────────┐
 │classificar_     │ erro? ─▶ resposta_erro
 │estoque (Python) │
 └───────┬─────────┘
         ▼
 ┌─────────────────┐
 │resposta_produto │ ─▶ END
 └─────────────────┘

O grafo é um DAG finito: todo caminho termina em END (condição de encerramento),
e a execução ainda é limitada por recursion_limit (ver agente.py).
"""

from __future__ import annotations

import re
from typing import Callable

from langgraph.graph import END, START, StateGraph

from agente_estoque import respostas
from agente_estoque.classificador import DadosInvalidos, classificar
from agente_estoque.config import Settings, get_settings
from agente_estoque.estado import EstadoAgente
from agente_estoque.estoque_tool import ErroEstoque, ProdutoEstoque
from agente_estoque.interpretacao import ErroInterpretador, Interpretador, validar_interpretacao

Consulta = Callable[[str], ProdutoEstoque]

_CONTROLE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def construir_grafo(interpretar: Interpretador, consultar: Consulta, settings: Settings | None = None):
    """Compila o grafo. `interpretar` (LLM) e `consultar` (ferramenta) são injetados."""
    settings = settings or get_settings()

    # ---------------- nós ----------------
    def validar_entrada(estado: EstadoAgente) -> dict:
        mensagem = estado.get("mensagem")
        if not isinstance(mensagem, str):
            return _erro("entrada_invalida", "A mensagem deve ser um texto.", "validar_entrada")
        mensagem = _CONTROLE.sub(" ", mensagem).strip()
        if not mensagem:
            return _erro("entrada_invalida", "A mensagem está vazia.", "validar_entrada")
        if len(mensagem) > settings.mensagem_max_chars:
            return _erro(
                "entrada_invalida",
                f"A mensagem excede {settings.mensagem_max_chars} caracteres.",
                "validar_entrada",
            )
        return {"mensagem": mensagem, "caminho": ["validar_entrada"]}

    def no_interpretar(estado: EstadoAgente) -> dict:
        mensagem = estado["mensagem"]
        try:
            bruta = interpretar(mensagem)  # <- decisão do LLM
        except ErroInterpretador as exc:
            return _erro(exc.tipo, str(exc), "interpretar")
        valida = validar_interpretacao(bruta, mensagem)  # <- validação determinística
        return {
            "intencao": valida.intencao,
            "codigo": valida.codigo,
            "motivo": valida.motivo,
            "caminho": ["interpretar"],
        }

    def no_consultar(estado: EstadoAgente) -> dict:
        try:
            produto = consultar(estado["codigo"])
        except ErroEstoque as exc:
            return {**_erro(exc.tipo, str(exc), "consultar_estoque"), "api_consultada": True}
        return {"api_consultada": True, "produto": produto.model_dump(), "caminho": ["consultar_estoque"]}

    def no_classificar(estado: EstadoAgente) -> dict:
        produto = estado["produto"]
        try:
            situacao = classificar(produto.get("quantidade_atual"), produto.get("estoque_minimo"))
        except DadosInvalidos as exc:
            return _erro("dados_invalidos", str(exc), "classificar_estoque")
        return {"situacao": situacao.value, "caminho": ["classificar_estoque"]}

    def resposta_produto(estado: EstadoAgente) -> dict:
        from agente_estoque.classificador import Situacao

        texto = respostas.resposta_produto(estado["produto"], Situacao(estado["situacao"]))
        return {"resposta": texto, "desfecho": "consulta_concluida", "caminho": ["resposta_produto"]}

    def resposta_esclarecimento(estado: EstadoAgente) -> dict:
        return {
            "resposta": respostas.resposta_esclarecimento(estado.get("motivo", "")),
            "desfecho": "esclarecimento",
            "caminho": ["resposta_esclarecimento"],
        }

    def resposta_fora_escopo(estado: EstadoAgente) -> dict:
        return {
            "resposta": respostas.resposta_fora_escopo(),
            "desfecho": "fora_de_escopo",
            "caminho": ["resposta_fora_escopo"],
        }

    def resposta_erro(estado: EstadoAgente) -> dict:
        return {
            "resposta": respostas.resposta_erro(estado["erro"], estado.get("codigo")),
            "desfecho": "erro",
            "caminho": ["resposta_erro"],
        }

    # ---------------- transições condicionais ----------------
    def apos_validacao(estado: EstadoAgente) -> str:
        return "resposta_erro" if estado.get("erro") else "interpretar"

    def apos_interpretacao(estado: EstadoAgente) -> str:
        """DECISÃO: usar a ferramenta (API) ou seguir outro caminho."""
        if estado.get("erro"):
            return "resposta_erro"
        return {
            "consultar_estoque": "consultar_estoque",
            "esclarecer": "resposta_esclarecimento",
            "fora_escopo": "resposta_fora_escopo",
        }.get(estado.get("intencao", ""), "resposta_erro")

    def se_erro_ou(proximo: str) -> Callable[[EstadoAgente], str]:
        return lambda estado: "resposta_erro" if estado.get("erro") else proximo

    # ---------------- montagem ----------------
    g = StateGraph(EstadoAgente)
    for nome, fn in {
        "validar_entrada": validar_entrada,
        "interpretar": no_interpretar,
        "consultar_estoque": no_consultar,
        "classificar_estoque": no_classificar,
        "resposta_produto": resposta_produto,
        "resposta_esclarecimento": resposta_esclarecimento,
        "resposta_fora_escopo": resposta_fora_escopo,
        "resposta_erro": resposta_erro,
    }.items():
        g.add_node(nome, fn)

    g.add_edge(START, "validar_entrada")
    g.add_conditional_edges(
        "validar_entrada", apos_validacao, {"interpretar": "interpretar", "resposta_erro": "resposta_erro"}
    )
    g.add_conditional_edges(
        "interpretar",
        apos_interpretacao,
        {
            "consultar_estoque": "consultar_estoque",
            "resposta_esclarecimento": "resposta_esclarecimento",
            "resposta_fora_escopo": "resposta_fora_escopo",
            "resposta_erro": "resposta_erro",
        },
    )
    g.add_conditional_edges(
        "consultar_estoque",
        se_erro_ou("classificar_estoque"),
        {"classificar_estoque": "classificar_estoque", "resposta_erro": "resposta_erro"},
    )
    g.add_conditional_edges(
        "classificar_estoque",
        se_erro_ou("resposta_produto"),
        {"resposta_produto": "resposta_produto", "resposta_erro": "resposta_erro"},
    )
    for terminal in ("resposta_produto", "resposta_esclarecimento", "resposta_fora_escopo", "resposta_erro"):
        g.add_edge(terminal, END)  # condição de encerramento explícita
    return g.compile()


def _erro(tipo: str, mensagem: str, no: str) -> dict:
    return {"intencao": "erro", "erro": {"tipo": tipo, "mensagem": mensagem}, "caminho": [no]}
