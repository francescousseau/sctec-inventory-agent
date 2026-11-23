# Checklist de entrega no AVA

**Prazo (enunciado, seção 3): 30/11/2026, até as 22h.** Libere folga: suba tudo até 29/11.

## Antes de submeter
- [x] Repositório **próprio** no GitHub (https://github.com/francescousseau/sctec-inventory-agent) (o repo `wangsouza/api-estoque` não substitui o seu).
- [x] Repositório acessível ao professor durante a avaliação (público).
- [x] `.env` **não** está no repositório; `git log -p | grep -i "api_key"` não mostra chave real.
- [ ] README preenchido: objetivo, arquitetura, tecnologias, configuração API + LLM, execução, n8n, exemplos, testes, limitações, **link do vídeo**, integrantes (se grupo).
- [ ] `n8n/workflow_estoque.json` presente e importável + evidência de execução (print/log em `evidencias/`).
- [x] `evidencias/cenarios_real.md` gerado **com LLM real** (`python scripts/executar_cenarios.py --llm real`). Os arquivos `*_simulado.*` são só apoio; renomeie/remova se preferir não confundir o avaliador.
- [x] `pytest` verde localmente (90 testes).
- [ ] Vídeo ≤ 5 min, com os 5 elementos (ver `docs/roteiro_video.md`), acessível por link.

## Submissão
- [ ] Colar no AVA: **link do repositório** + **link do vídeo**.
- [ ] Se for **grupo**: *cada integrante* submete individualmente o MESMO link do vídeo e do repositório; README identifica todos e suas contribuições.
- [ ] Abrir os dois links em uma aba anônima para confirmar o acesso.

## Atenção (critério de plágio = nota 0)
Você pode se basear em outras soluções, mas não copiar. Este pacote foi gerado com apoio de IA: **leia, execute e entenda cada arquivo**, adapte nomes/mensagens e documente no README as suas decisões. Esteja preparado para explicar qualquer trecho.
