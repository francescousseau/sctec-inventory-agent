"""CLI: python -m agente_estoque "Como está o estoque do PRD-001?" [--json]"""

import argparse
import json
import logging
import sys

from agente_estoque.agente import criar_agente, executar
from agente_estoque.interpretacao import ErroInterpretador


def main() -> int:
    parser = argparse.ArgumentParser(prog="agente_estoque", description="Agente de análise de estoque")
    parser.add_argument("mensagem", help="Pergunta em linguagem natural")
    parser.add_argument("--json", action="store_true", help="Imprime o estado final completo")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mostra logs de execução")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(message)s")

    try:
        grafo = criar_agente()
    except ErroInterpretador as exc:
        print(f"Configuração: {exc}", file=sys.stderr)
        return 2
    estado = executar(grafo, args.mensagem)
    if args.json:
        print(json.dumps(estado, ensure_ascii=False, indent=2, default=str))
    else:
        print(estado["resposta"])
        print(f"\n[desfecho={estado['desfecho']} | api_consultada={estado['api_consultada']} | caminho={' → '.join(estado['caminho'])}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
