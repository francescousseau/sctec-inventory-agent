# Matriz de rastreabilidade — critérios do enunciado × implementação

Pesos lidos das colunas da tabela de avaliação do enunciado (máx. por critério). Soma = 10,0.
Legenda de evidência: ✅ executado neste ambiente · 🟡 executado com simulação (ver nota) · ⏳ pendente (depende de você).

| # | Critério (máx.) | Onde está atendido | Comportamento / evidência | Status |
|---|---|---|---|---|
| 1 | Compreensão do problema e funcionamento (1,0) | `agente_estoque/` completo; `classificador.py`; `respostas.py` | Consulta produto e classifica disponível/baixo/esgotado com dados da API; `evidencias/cenarios_real.md` (Gemini real; cenários 1, 4, 5, 6 conferidos com `curl` direto à API) | ✅ |
| 2 | Agente com LLM e LangGraph (2,0) | `grafo.py` (nós, aresta condicional, `END`); `estado.py` (estado tipado); `interpretacao.py` + `instrucoes.py` (LLM + prompt com papel/objetivo/contexto/restrições) | 8 nós, 4 arestas condicionais; decisão "consultar × esclarecer × encerrar" em `apos_interpretacao`; `tests/test_grafo.py` (caminhos e término). Cliente Gemini testado com dublê (saída estruturada e erros de autenticação/cota) em `tests/test_interpretacao.py`; execução com Gemini real em `evidencias/cenarios_real.md` (11/11) | ✅ |
| 3 | Ferramenta Python + API (1,5) | `estoque_tool.py::buscar_produto` | GET somente leitura, timeout, retentativa só p/ rede, valida código (regex) e estrutura do retorno; trata 404, 422, 503, 5xx, timeout, JSON inválido, redirecionamento. `tests/test_estoque_tool.py` + `tests/test_integracao_api.py` contra a API real do professor | ✅ |
| 4 | Automação n8n (1,5) | `n8n/workflow_estoque.json` | Webhook → HTTP (agente) → Set → Respond. Executado via Docker Compose (n8n 2.48.8 + agente em contêiner + Gemini real): `evidencias/n8n_execucao.md` (7 chamadas, inclui agente desligado) + prints do editor | ✅ |
| 5 | Confiabilidade, segurança, supervisão (1,0) | `grafo.py::validar_entrada`; `interpretacao.py::validar_interpretacao`; `config.py` + `.env.example` + `.gitignore`; `respostas.py` | Entrada validada (vazia/longa/controle); saída do LLM validada (código deve existir no texto); falhas → resposta controlada sem classificar; grafo finito + `recursion_limit`; segredos só em env; agente **somente leitura** (sem POST ⇒ sem ação sensível; confirmação humana não se aplica) | ✅ |
| 6 | Evidências de 3 cenários (1,0) | `scripts/executar_cenarios.py`; `evidencias/`; `docs/testes.md` | 1: PRD-001 baixo · 2: PRD-999 inexistente · 3: PRD-503/API offline. +7 complementares; `evidencias/cenarios_real.md` com Gemini real (11/11) | ✅ |
| 7 | Documentação / README (1,0) | `README.md` | Objetivo, arquitetura, tecnologias, execução, n8n, testes, limitações | ✅ (preencher link do vídeo) |
| 8 | Vídeo ≤ 5 min (1,0) | `docs/roteiro_video.md` | Roteiro cronometrado (4:45) com os 5 elementos | ⏳ gravar |

## Pontos do enunciado que estavam truncados no Markdown anexo
Não consegui ler integralmente, então tratei como **propostas minhas** (ajuste se o PDF original disser outra coisa):
- Tabela "Testes mínimos" (§4.6): só aparecem os números 1–3 e fragmentos; usei os cenários propostos no seu briefing.
- "Fluxo de referência" (§5.1) cortado em `Solicitação → LangGraph/LLM → Decisão → Ferramenta/API (quand…`; mantive esse fluxo.
- Descrições das colunas intermediárias/máximas da tabela de avaliação estão parciais; os pesos acima vêm dos cabeçalhos numéricos.

## Decisões próprias (propostas de implementação)
1. **Um provedor**: Gemini Developer API (Google AI Studio) via `langchain-google-genai` (`GOOGLE_API_KEY`, `GEMINI_MODEL`), com saída estruturada para a intenção.
2. **LLM só interpreta**; consulta, classificação e texto final são em Python (nenhum dado da API volta ao LLM ⇒ sem injeção por dados).
3. **Um produto por vez, por código**: consulta por nome gera pedido de esclarecimento (não há busca por nome na API de leitura individual).
4. Fronteira `quantidade == mínimo` ⇒ **baixo** (confirmado no README da API, §5).
5. Porta 8001 para o agente (a API do professor usa 8000).
