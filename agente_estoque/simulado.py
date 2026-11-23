"""Interpretador SIMULADO (regras fixas) — usado apenas em testes e no script de
cenários com --llm simulado. NÃO é um LLM e o servidor nunca o utiliza.

Serve para validar o grafo, a ferramenta e a API sem depender de credenciais.
Qualquer evidência produzida com ele deve ser rotulada como "simulada".
"""

from agente_estoque.interpretacao import Interpretacao, codigos_na_mensagem

_VERBOS_PROIBIDOS = ("cadastr", "apag", "exclu", "delet", "altere", "atualiz", "ignore", "esqueç", "esqueca", "compre")
_PALAVRAS_ESTOQUE = (
    "estoque", "produto", "quantidade", "mouse", "teclado", "cabo", "monitor",
    "webcam", "notebook", "papel", "caneta", "cartucho", "pen drive", "álcool",
)


def interpretador_simulado(mensagem: str) -> Interpretacao:
    baixo = mensagem.lower()
    if any(v in baixo for v in _VERBOS_PROIBIDOS):
        return Interpretacao(intencao="fora_escopo", motivo="[simulado] pedido de alteração")
    codigos = sorted(codigos_na_mensagem(mensagem))
    if codigos:
        return Interpretacao(intencao="consultar_estoque", codigo=codigos[0], motivo="[simulado]")
    if any(p in baixo for p in _PALAVRAS_ESTOQUE):
        return Interpretacao(intencao="esclarecer", motivo="[simulado] sem código")
    return Interpretacao(intencao="fora_escopo", motivo="[simulado] assunto não relacionado")
