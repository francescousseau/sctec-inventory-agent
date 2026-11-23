# Evidência da troca de dados n8n ↔ aplicação Python

- Gerado em: 2026-11-23T11:08:15
- Executado com `docker compose up --build -d`: n8n 2.48.8 (contêiner `sctec-n8n`) e agente Python (contêiner `sctec-agente-estoque`), workflow `n8n/workflow_estoque.json` importado e **publicado** sem alterações (nó HTTP → `http://agente:8001/analisar`).
- LLM **real**: Gemini Developer API, modelo `gemini-3.5-flash-lite`. API do professor (clone oficial) no host em `:8000`, acessada pelo agente via `host.docker.internal`.
- O n8n só chama a interface HTTP do agente; interpretação, consulta e classificação ficam no Python.

Comando: `curl -X POST http://127.0.0.1:5678/webhook/estoque -H 'Content-Type: application/json' -d '{"mensagem":"..."}'`

## `Como está o estoque do PRD-001?`

HTTP 200

```json
{
  "resposta": "Produto PRD-001 — Mouse sem fio (Periféricos)\nQuantidade disponível: 5 un | Estoque mínimo: 10 un\nSituação: ESTOQUE BAIXO (quantidade 5 ≤ mínimo 10).\nFonte: GET /produtos/PRD-001 da API de estoque.",
  "desfecho": "consulta_concluida",
  "codigo": "PRD-001",
  "situacao": "baixo",
  "requer_atencao": true,
  "api_consultada": true,
  "caminho": "validar_entrada > interpretar > consultar_estoque > classificar_estoque > resposta_produto"
}
```

## `Como está o estoque do PRD-004?`

HTTP 200

```json
{
  "resposta": "Produto PRD-004 — Cabo HDMI 2 m (Cabos e Adaptadores)\nQuantidade disponível: 0 un | Estoque mínimo: 20 un\nSituação: ESGOTADO (quantidade igual a zero).\nFonte: GET /produtos/PRD-004 da API de estoque.",
  "desfecho": "consulta_concluida",
  "codigo": "PRD-004",
  "situacao": "esgotado",
  "requer_atencao": true,
  "api_consultada": true,
  "caminho": "validar_entrada > interpretar > consultar_estoque > classificar_estoque > resposta_produto"
}
```

## `Como está o estoque do PRD-503?`

HTTP 200

```json
{
  "resposta": "A API de estoque está indisponível no momento. Sem os dados não posso informar a situação do produto PRD-503; tente novamente mais tarde.",
  "desfecho": "erro",
  "codigo": "PRD-503",
  "situacao": "",
  "requer_atencao": false,
  "api_consultada": true,
  "caminho": "validar_entrada > interpretar > consultar_estoque > resposta_erro"
}
```

## `Quanto temos do produto PRD-999?`

HTTP 200

```json
{
  "resposta": "Não encontrei o produto PRD-999 no estoque. Confira o código e tente novamente.",
  "desfecho": "erro",
  "codigo": "PRD-999",
  "situacao": "",
  "requer_atencao": false,
  "api_consultada": true,
  "caminho": "validar_entrada > interpretar > consultar_estoque > resposta_erro"
}
```

## `Tem mouse sem fio no estoque?`

HTTP 200

```json
{
  "resposta": "Preciso do código do produto no formato PRD-XXX (ex.: PRD-001) para consultar o estoque. Consulto um produto por vez.\nMotivo: há produto citado pelo nome, mas sem código PRD-XXX.",
  "desfecho": "esclarecimento",
  "codigo": "",
  "situacao": "",
  "requer_atencao": false,
  "api_consultada": false,
  "caminho": "validar_entrada > interpretar > resposta_esclarecimento"
}
```

## `Qual é a capital da França?`

HTTP 200

```json
{
  "resposta": "Só consigo consultar a situação de estoque (disponível, baixo ou esgotado) de um produto, a partir do código PRD-XXX (ex.: PRD-001). Não realizo cadastros, alterações ou outros assuntos.",
  "desfecho": "fora_de_escopo",
  "codigo": "",
  "situacao": "",
  "requer_atencao": false,
  "api_consultada": false,
  "caminho": "validar_entrada > interpretar > resposta_fora_escopo"
}
```

## `Como está o estoque do PRD-001? [agente Python DESLIGADO]`

HTTP 200

```json
{
  "resposta": "O agente de estoque está indisponível no momento.",
  "desfecho": "agente_indisponivel",
  "codigo": "",
  "situacao": "",
  "requer_atencao": false,
  "api_consultada": false,
  "caminho": ""
}
```
