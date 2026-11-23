# Evidência da troca de dados n8n ↔ aplicação Python

- Gerado em: 2026-11-23T09:07:27
- n8n 2.35.7 (npm) executado localmente, workflow `n8n/workflow_estoque.json` importado e **publicado** (URL do nó HTTP trocada de `host.docker.internal` para `127.0.0.1`, pois não havia contêiner).
- Agente Python em `:8001` e API do professor (clone oficial) em `:8000`.
- **Ressalva:** o interpretador usado foi um *servidor OpenAI-compatível falso* (sem LLM real). A troca Webhook → n8n → Python → API é real; a interpretação do LLM é simulada. Refazer com o LLM real antes da entrega.

Comando: `curl -X POST http://127.0.0.1:5678/webhook/estoque -H 'Content-Type: application/json' -d '{"mensagem":"..."}'`

## `Como está o estoque do PRD-001?`

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

## `Qual é a capital da França?`

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
