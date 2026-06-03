# 📊 progress.md — Registro de Progresso

> **Projeto:** Aloogaí | **Protocolo:** V.L.A.E.G.S.

---

## Sessão 1 — 2026-06-01 (Inicialização)

### ✅ Concluído
- [x] Leitura e análise dos arquivos do projeto (`protocolo_vlaegs.md`, `Instrucoes_Claude_Aloogai.md`)
- [x] Execução do **Protocolo 0 (Inicialização)** do V.L.A.E.G.S.
- [x] **Fase 1 (Visão):** 5 Perguntas de Descoberta respondidas pelo usuário
- [x] Pesquisa de stack tecnológico (React Native vs Flutter, gateways BR, deploy, referências)
- [x] Criação do `gemini.md` (Constituição do Projeto)
- [x] Criação do `findings.md` (Pesquisas e Descobertas)
- [x] Criação do `progress.md` (este arquivo)
- [x] Criação do `task_plan.md` (Blueprint com fases e checklists)
- [x] Blueprint APROVADO pelo usuário

### ❌ Erros / Bloqueios
- Nenhum.

---

## Sessão 2 — 2026-06-01 ~ 2026-06-02 (Sprint 1.1 + 1.2 + Validação)

### ✅ Concluído
- [x] **Sprint 1.1 — Scaffolding:** 85+ arquivos criados no `backend/`
  - Config: settings (base/dev/prod), urls, asgi, wsgi, celery, routing
  - Requirements: base.txt, dev.txt, prod.txt
  - Infra: manage.py, .env.example, .gitignore
- [x] **Sprint 1.2 — Modelagem de Dados:** 7 Django apps completas
  - `users/` — 8 arquivos (models, admin, serializers, views, urls, managers)
  - `catalog/` — 8 arquivos (models, admin, serializers, views, urls, filters)
  - `rentals/` — 9 arquivos (models, admin, serializers, views, urls, services, signals)
  - `payments/` — 8 arquivos (models, admin, serializers, views, urls, services)
  - `chat/` — 10 arquivos (models, admin, serializers, views, urls, consumers, routing, middleware)
  - `esg/` — 10 arquivos (models, admin, serializers, views, urls, services, signals, seed_selos command)
  - `notifications/` — 8 arquivos (models, admin, serializers, views, urls, services)
- [x] **Sprint 1.3 — Autenticação JWT:** Já implementada nos serializers/views de users + config JWT
- [x] **Sprint 1.4 — Busca Geoespacial:** Já implementada no catalog views com ST_DWithin
- [x] **Módulo de Compatibilidade GIS** (`apps/core/geo_compat.py`): Fallback para SQLite em dev
- [x] **Validação do Ambiente:**
  - ✅ `python -m venv venv` — Virtual environment criado
  - ✅ `pip install` — 30 pacotes instalados (Django 6.0.5, DRF 3.17.1, channels 4.3.2, stripe 15.2.0)
  - ✅ `manage.py check` — **System check identified no issues (0 silenced)**
  - ✅ `manage.py makemigrations` — **31 migrations geradas** para todas as 7 apps
  - ✅ `manage.py migrate` — **Todas as migrations aplicadas com sucesso**
  - ✅ `manage.py runserver` — **Servidor rodou com sucesso** na porta 8000

### ❌ Erros / Bloqueios (Resolvidos)
- 3 subagentes caíram por limite de quota (RESOURCE_EXHAUSTED) — arquivos completados manualmente
- GDAL não disponível no Windows — resolvido com módulo `geo_compat.py` (fallback SQLite)
- `rest_framework_gis` importava GDAL no `ready()` — resolvido removendo do INSTALLED_APPS em modo SQLite
- `DocumentoKYCInline` precisava de `fk_name` — resolvido (2 ForeignKeys para Usuario)
- `apps.payments.webhook_urls` não existia — resolvido com import direto da view

### 📝 Notas
- Em produção (PostGIS + GDAL), setar `USE_SQLITE=False` no `.env` para ativar campos geoespaciais reais
- O warning `django-fsm` deprecated é cosmético — a lib funciona normalmente com Django 6
- Próximo passo: Fase 2 (Motor Financeiro Stripe) ou Fase 4 (App Mobile React Native)

---

## Sessão 3 — 2026-06-02 (Skills)

### ✅ Concluído
- [x] **Skill `aloogai-code-standards`** criada em `~/.gemini/config/skills/aloogai-code-standards/SKILL.md`
  - Padrões de nomenclatura pt-BR, UUID PKs, GIS via geo_compat
  - Invariantes de negócio (caução, split, FSM, chat condicionado)
  - Templates de models, serializers, views, services
  - Checklist de revisão obrigatório
- [x] **Skill `aloogai-django-app`** criada em `~/.gemini/config/skills/aloogai-django-app/SKILL.md`
  - Template de scaffold para novas apps Django
  - Estrutura de 11 passos com todos os arquivos padrão
  - Checklist pós-criação com validação automática

---

## Sessão 4 — 2026-06-02~03 (Fase 2 — Motor Financeiro)

### ✅ Concluído
- [x] **Gap 6 — Fix StatusOnboarding:** Adicionado `COMPLETO` ao choices (alinhado com webhook handler)
- [x] **Gap 3 — Registro de Transações:** Método `_registrar_transacao()` no `StripeService`
  - Cada operação Stripe (pre-auth, captura, liberação, caução) agora cria um registro `TransacaoStripe`
  - Rastreabilidade completa de todas as operações financeiras
- [x] **Gap 1 — Integração create → Stripe:** `perform_create` agora:
  - Chama `StripeService.criar_pre_autorizacao()` automaticamente
  - Salva `payment_intent_id` na locação
  - Transiciona FSM de SOLICITADO → CAUCAO_RETIDA
- [x] **Gap 2 — Integração concluir → Stripe:** Ação `concluir` agora:
  - Captura pagamento das diárias via `capturar_pagamento_diarias()`
  - Libera caução via `liberar_caucao()`
  - Retorna 502 se houver erro financeiro
- [x] **Gap 4 — Celery Task de Expiração:** `rentals/tasks.py` criado
  - Task `expirar_solicitacoes_pendentes` cancela locações SOLICITADO > 24h
- [x] **Gap 5 — Testes Unitários:** 3 arquivos de teste criados
  - `conftest.py` — 4 factories (Usuario, Categoria, Item, Locacao)
  - `test_services.py` — 11 testes (cálculos, validação, disponibilidade)
  - `test_models.py` — 24 testes (FSM: transições válidas, inválidas, contestação, cancelamento)
- [x] **Migration `0003`:** StatusOnboarding atualizado e aplicado
- [x] **Dependências:** `factory-boy` e `faker` instalados

### 📊 Resultados de Verificação
- ✅ `manage.py check` — **0 issues**
- ✅ `manage.py test` — **35 testes passando (19.1s)**
- ✅ `manage.py migrate` — Migration `payments.0003` aplicada

### 📝 Notas
- As chamadas Stripe são mockadas em dev (sem STRIPE_SECRET_KEY real)
- Em produção, basta configurar as chaves Stripe no `.env`

---

## Sessão 5 — 2026-06-03 (Fase 3 — Chat Real-Time)

### ✅ Concluído
- [x] **Fix `SalaChatViewSet.get_queryset()`**: Reescrito de código confuso para `Q(locador=user) | Q(locatario=user)` limpo
- [x] **`CHAT_ENCRYPTION_KEY` configurada**: Chave Fernet real gerada e adicionada ao `dev.py`
- [x] **Signal `criar_sala_chat_para_locacao`**: Criação automática de `SalaChat` ao criar `Locacao`
  - Registrado em `apps.py` via `ready()` 
- [x] **ChatConsumer melhorado**: Roteamento por ações (mensagem/digitando/marcar_lida)
  - Evento "digitando" efêmero (broadcast sem persistir)
  - Marcar como lida via WebSocket
  - Handler `chat_digitando` filtra para não enviar ao próprio remetente
- [x] **19 testes unitários do chat criados**:
  - Permissões de sala (5 testes)
  - Participantes (4 testes)
  - Criptografia (1 teste)
  - Leitura de mensagens (3 testes)
  - Status de ordem (3 testes)
  - Criação automática via signal (3 testes)

### 📊 Resultados de Verificação
- ✅ `manage.py check` — **0 issues**
- ✅ `manage.py test` — **54 testes passando (32.7s)** (35 rentals + 19 chat)

### 📝 Notas
- Consumer suporta 3 ações: `mensagem`, `digitando`, `marcar_lida`
- Mensagens criptografadas em repouso (AES-256 / Fernet)
- Channel Layer usa InMemoryChannelLayer em dev, Redis em produção

---

## Sessão 6 — 2026-06-03 (Fase 4 Mobile + Fase 5 ESG)

### ✅ Fase 5 — Módulo ESG — Concluída
- [x] **18 testes unitários do ESG criados** (`esg/tests/test_services.py`):
  - FatorESGCategoria (3 testes): fórmula CO₂, valores, __str__
  - Cálculo CO₂ (3 testes): com fator, sem fator (padrão), mínimo 1 dia
  - Score ESG (2 testes): incremento, acumulativo
  - Histórico ESG (2 testes): registro, __str__
  - Selos/Gamificação (4 testes): sem selos, desbloqueio por score, anti-duplicação, __str__
  - Pipeline completo (4 testes): resumo, co2_evitado, histórico, locador 50%
- [x] **Fix `refresh_from_db()`** — Conflito com django-fsm resolvido (query direta)

### 📊 Resultados de Verificação (Backend Completo)
- ✅ `manage.py check` — **0 issues**
- ✅ `manage.py test` — **72 testes passando (42s)**
  - 35 rentals + 19 chat + 18 ESG

### 🔄 Fase 4 — App Mobile — Em Progresso (Subagente)
- Sprint 4.1 (Scaffolding + Design System): delegado ao subagente
- Sprint 4.2 (Auth + Login/Registro): delegado ao subagente
- Paleta de cores extraída da logo (verde→amarelo→laranja)
- Suporte Dark/Light mode definido no plano
