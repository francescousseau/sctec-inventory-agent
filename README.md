# Agente de Análise de Estoque — SCTEC C1 · Agentes de IA T2

> **Integrantes:** _preencha (nome — contribuição)_ · **Vídeo demonstrativo:** _cole aqui o link (≤ 5 min)_

## 1. Problema e objetivo
Responder, em linguagem natural, se um produto está **disponível**, com **estoque baixo** ou **esgotado**, consultando a API de estoque simulada do professor. Toda conclusão é verificável: a resposta sempre mostra produto, quantidade, mínimo e a regra aplicada, a partir dos dados retornados pela API.

## 2. Tecnologias
Python 3.11+ · LangGraph · LangChain (`langchain-google-genai`, cliente do Gemini) · FastAPI/uvicorn (interface HTTP) · httpx · Pydantic · n8n · pytest.

**Provedor de LLM (decisão):** Gemini Developer API (Google AI Studio), via `ChatGoogleGenerativeAI` do `langchain-google-genai`.
- `GOOGLE_API_KEY`: chave criada em <https://aistudio.google.com/apikey> (obrigatória; sem ela o agente responde com erro de configuração).
- `GEMINI_MODEL`: modelo usado (padrão `gemini-2.5-flash-lite`). Chaves criadas recentemente no AI Studio recebem 404 nesse modelo; nesse caso use `GEMINI_MODEL=gemini-3.5-flash-lite`.
- A intenção é obtida com **saída estruturada** (`with_structured_output(Interpretacao)`): o Gemini devolve um objeto validado pelo schema Pydantic (`intencao`, `codigo`, `motivo`), e as regras em Python (`validar_interpretacao`) ainda conferem o código antes de qualquer consulta.
- Erros do Gemini têm desfechos distintos em `erro.tipo`: `llm_autenticacao` (chave inválida/sem permissão — o AI Studio devolve 400 `API_KEY_INVALID` ou 401/403), `llm_cota_excedida` (429 `RESOURCE_EXHAUSTED`), `llm_modelo_indisponivel` (404: modelo inexistente para a chave), `llm_indisponivel` (rede/outras falhas) e `saida_llm_invalida` (resposta fora do schema).

## 3. Arquitetura
```mermaid
flowchart TD
  S([START]) --> V[validar_entrada]
  V -->|inválida| E[resposta_erro]
  V --> I["interpretar<br/>(LLM + validação em Python)"]
  I -->|erro do LLM| E
  I -->|esclarecer| RE[resposta_esclarecimento]
  I -->|fora_escopo| RF[resposta_fora_escopo]
  I -->|consultar_estoque| C["consultar_estoque<br/>(ferramenta → API)"]
  C -->|erro| E
  C --> K["classificar_estoque<br/>(Python)"]
  K -->|dados inválidos| E
  K --> RP[resposta_produto]
  RP --> F([END]); RE --> F; RF --> F; E --> F
```
- **Estado** (`estado.py`): `EstadoAgente` tipado (mensagem, intenção, código, produto, situação, erro, resposta, `caminho`).
- **Decisão condicional** (`grafo.py::apos_interpretacao`): consultar a API × pedir esclarecimento × encerrar fora de escopo.
- **Encerramento:** grafo finito (DAG); todos os caminhos chegam a `END`; execução ainda limitada por `recursion_limit=12`.
- **Papel do LLM:** só interpreta (intenção + código). Consulta, classificação e texto final são Python ⇒ ele não inventa situação de estoque. A saída do LLM é validada: o código deve seguir `PRD-XXX`, aparecer **literalmente** na mensagem e ser o único; senão rebaixa para esclarecimento.
- **Dados da API nunca voltam ao LLM** (o LLM só vê a mensagem do usuário, delimitada em `<mensagem_usuario>`), evitando injeção por dados.

### Ferramenta de estoque (`estoque_tool.py::buscar_produto`)
| Item | Definição |
|---|---|
| Finalidade | `GET {ESTOQUE_API_URL}/produtos/{codigo}` (somente leitura) |
| Parâmetro | `codigo`: `PRD-XXX` (regex `PRD-[0-9]{3}`, validado antes de montar a URL) |
| Retorno | `ProdutoEstoque` (codigo, nome, categoria, quantidade_atual, estoque_minimo, unidade), validado com tipos estritos |
| Falhas | `CodigoInvalido`, `ProdutoNaoEncontrado` (404), `ServicoIndisponivel` (503/5xx/timeout/conexão), `RespostaInvalida` (JSON/estrutura/status inesperado/produto divergente) |
| Robustez | timeout; 1 retentativa só em falha de rede; sem redirecionamentos; URL-base configurável e fixa |

### Regra de classificação (`classificador.py`) — confirmada no README da API (§5)
| Condição | Situação |
|---|---|
| `quantidade == 0` | **Esgotado** |
| `0 < quantidade <= mínimo` | **Baixo** (igual ao mínimo conta como baixo) |
| `quantidade > mínimo` | **Disponível** |

Dados ausentes/negativos/de tipo errado ⇒ erro controlado, sem classificação presumida.

## 4. Configuração e execução
```bash
# 1) API do professor (porta 8000)
git clone https://github.com/wangsouza/api-estoque.git && cd api-estoque
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000      # Swagger: http://127.0.0.1:8000/docs

# 2) Este projeto
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # preencha GOOGLE_API_KEY (GEMINI_MODEL é opcional)
# fora do Docker, aponte para a API local: ESTOQUE_API_URL=http://127.0.0.1:8000

# 3) Uso
python -m agente_estoque "Como está o estoque do PRD-001?"            # CLI
uvicorn --factory agente_estoque.servidor:criar_app --port 8001       # interface HTTP
curl -s -X POST localhost:8001/analisar -H 'Content-Type: application/json' \
     -d '{"mensagem":"Como está o estoque do PRD-004?"}'
```

### Execução com Docker Compose
Com Docker Desktop ativo e a API do professor em `127.0.0.1:8000`:

```bash
cp .env.example .env
# preencha GOOGLE_API_KEY no arquivo .env
docker compose up --build -d
```

Serviços disponíveis:

- Agente: `http://localhost:8001/health`
- n8n: `http://localhost:5678`
- API do professor: `http://localhost:8000`

No n8n, importe `n8n/workflow_estoque.json` e publique/ative o workflow.
O workflow usa `http://agente:8001/analisar` na rede interna do Compose.
O Compose usa `host.docker.internal` para o agente alcançar a API do host.
Para parar: `docker compose down`. Os dados do n8n ficam no volume `n8n-data`.
**Windows (PowerShell):** troque `source .venv/bin/activate` por `.venv\Scripts\Activate.ps1`; para `curl` use `curl.exe` ou o Swagger do agente em `http://127.0.0.1:8001/docs`.

### Exemplo de resposta
```text
Produto PRD-001 — Mouse sem fio (Periféricos)
Quantidade disponível: 5 un | Estoque mínimo: 10 un
Situação: ESTOQUE BAIXO (quantidade 5 ≤ mínimo 10).
Fonte: GET /produtos/PRD-001 da API de estoque.
```
A resposta HTTP (`POST /analisar`) inclui também `desfecho`, `situacao`, `produto`, `api_consultada` e `caminho` (nós percorridos) para auditoria.

## 5. Automação n8n (`n8n/workflow_estoque.json`)
**Finalidade:** expor o agente por Webhook. **Fluxo:** `Webhook (POST /webhook/estoque)` → `HTTP Request (POST /analisar do agente)` → `Set (monta resposta + requer_atencao)` → `Respond to Webhook`. O n8n não decide nada: LLM, estado, ferramenta e classificação ficam no LangGraph. Se o agente estiver fora do ar, o n8n responde com `desfecho: agente_indisponivel`.

1. Importe o JSON (Workflows → Import from file) e ative o workflow.
2. **URL do nó HTTP:** o arquivo usa `http://agente:8001/analisar` (nome do serviço na rede do Docker Compose). Com n8n em contêiner avulso, troque por `http://host.docker.internal:8001/analisar`; com n8n direto no host (npm), por `http://127.0.0.1:8001/analisar`.
3. Docker no Linux: `docker run --add-host=host.docker.internal:host-gateway -p 5678:5678 n8nio/n8n` e inicie o agente com `--host 0.0.0.0` (a API não tem autenticação: só em ambiente de desenvolvimento controlado).
4. Teste: `curl -X POST http://127.0.0.1:5678/webhook/estoque -H 'Content-Type: application/json' -d '{"mensagem":"Como está o estoque do PRD-004?"}'` (em modo de teste do editor, use `/webhook-test/estoque`).

Evidência: `evidencias/n8n_execucao.md`.

## 6. Confiabilidade, segurança e supervisão
- Validação de entrada (vazia, longa, caracteres de controle) e de parâmetros da ferramenta.
- Falhas (404, 503, rede, resposta inválida, LLM sem autenticação/sem cota/indisponível/ilegível) ⇒ resposta controlada, **sem classificar nem inventar**.
- Condição de parada: grafo finito + `recursion_limit`.
- Credenciais só em variáveis de ambiente; `.env` ignorado no Git; chave nunca é logada.
- Limites de atuação: o agente é **somente leitura** (o `POST /produtos` da API não é exposto); pedidos de cadastro/alteração/“ignore as regras” encerram sem consultar a API. Por não haver ação que modifique dados, não há etapa de confirmação humana a demonstrar.

## 7. Testes
`python -m pytest -v` (90 testes; os de integração exigem a API em `:8000`) e `python scripts/executar_cenarios.py --llm real` (cenários com entrada, esperado, observado e dados brutos da API; resultado com Gemini real em [`evidencias/cenarios_real.md`](evidencias/cenarios_real.md), 11/11). Detalhes e resultados: [`docs/testes.md`](docs/testes.md); matriz de critérios: [`docs/matriz_rastreabilidade.md`](docs/matriz_rastreabilidade.md).

## 8. Limitações
- Consulta **um produto por vez, por código `PRD-XXX`**; perguntas só pelo nome pedem o código (não há busca por nome).
- Não lista nem compara produtos; não cadastra (decisão de escopo/segurança).
- Qualidade da interpretação depende do LLM escolhido; a validação em Python impede consultas com códigos que não estejam no texto, mas pode pedir esclarecimento em casos como “prd 1”.
- Sem autenticação entre n8n e agente (uso didático local).
- Depende da disponibilidade da Gemini API: em picos de demanda ela devolve 503; o agente tenta até 3 vezes com backoff e, se persistir, responde `llm_indisponivel` sem consultar nem classificar.

## 9. Estrutura
```
agente_estoque/  config · instrucoes · interpretacao · estoque_tool · classificador
                 estado · grafo · respostas · agente · servidor · __main__ · simulado(*)
n8n/workflow_estoque.json     scripts/executar_cenarios.py     tests/     evidencias/     docs/
(*) interpretador de regras usado só em testes/cenários simulados; o servidor nunca o usa.
```
