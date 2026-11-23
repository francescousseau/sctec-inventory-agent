"""Redação das respostas ao usuário (determinística, sempre baseada nos dados)."""

from agente_estoque.classificador import ROTULOS, Situacao

FORMATO_CODIGO = "PRD-XXX (ex.: PRD-001)"

MENSAGENS_ERRO = {
    "produto_nao_encontrado": "Não encontrei o produto {codigo} no estoque. Confira o código e tente novamente.",
    "servico_indisponivel": (
        "A API de estoque está indisponível no momento. Sem os dados não posso informar a "
        "situação do produto {codigo}; tente novamente mais tarde."
    ),
    "resposta_invalida": (
        "A API de estoque respondeu em um formato inesperado; por isso não vou informar a "
        "situação do produto {codigo}."
    ),
    "codigo_invalido": f"O código informado não segue o padrão {FORMATO_CODIGO}.",
    "dados_invalidos": (
        "Os dados de quantidade/mínimo do produto {codigo} estão inconsistentes; "
        "não faço classificação presumida."
    ),
    "llm_indisponivel": "Não consegui interpretar sua solicitação agora (serviço de linguagem indisponível).",
    "llm_autenticacao": (
        "O agente não conseguiu se autenticar no serviço de linguagem (Gemini). "
        "Verifique a GOOGLE_API_KEY."
    ),
    "llm_modelo_indisponivel": (
        "O modelo de linguagem configurado não está disponível para esta chave. "
        "Revise GEMINI_MODEL no .env."
    ),
    "llm_cota_excedida": (
        "O limite de uso do serviço de linguagem (Gemini) foi atingido. "
        "Aguarde alguns instantes e tente novamente."
    ),
    "saida_llm_invalida": "Não consegui interpretar sua solicitação com segurança. Reformule, citando o código PRD-XXX.",
    "configuracao_ausente": "O agente não está configurado com um LLM (veja .env.example).",
}


def resposta_produto(produto: dict, situacao: Situacao) -> str:
    q, m, un = produto["quantidade_atual"], produto["estoque_minimo"], produto["unidade"]
    if situacao is Situacao.ESGOTADO:
        regra = "quantidade igual a zero"
    elif situacao is Situacao.BAIXO:
        regra = f"quantidade {q} ≤ mínimo {m}" + (" (igual ao mínimo conta como baixo)" if q == m else "")
    else:
        regra = f"quantidade {q} > mínimo {m}"
    return (
        f"Produto {produto['codigo']} — {produto['nome']} ({produto['categoria']})\n"
        f"Quantidade disponível: {q} {un} | Estoque mínimo: {m} {un}\n"
        f"Situação: {ROTULOS[situacao]} ({regra}).\n"
        f"Fonte: GET /produtos/{produto['codigo']} da API de estoque."
    )


def resposta_esclarecimento(motivo: str = "") -> str:
    base = (
        f"Preciso do código do produto no formato {FORMATO_CODIGO} para consultar o estoque. "
        "Consulto um produto por vez."
    )
    return f"{base}\nMotivo: {motivo}." if motivo else base


def resposta_fora_escopo() -> str:
    return (
        "Só consigo consultar a situação de estoque (disponível, baixo ou esgotado) de um produto, "
        f"a partir do código {FORMATO_CODIGO}. Não realizo cadastros, alterações ou outros assuntos."
    )


def resposta_erro(erro: dict, codigo: str | None) -> str:
    tipo = erro.get("tipo", "")
    modelo = MENSAGENS_ERRO.get(tipo)
    if modelo is None:  # ex.: entrada_invalida — a mensagem já é segura e específica
        return erro.get("mensagem", "Não foi possível concluir a solicitação.")
    return modelo.format(codigo=codigo or "informado")
