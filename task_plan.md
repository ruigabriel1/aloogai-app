# 🗺️ task_plan.md — Blueprint do Projeto Aloogaí

> **Protocolo:** V.L.A.E.G.S. | **Status:** ⏳ AGUARDANDO APROVAÇÃO
> **Objetivo MVP:** App publicado nas lojas com cadastro, mapa de proximidade e chat funcional

---

## Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    APLICATIVO MOBILE                         │
│            React Native (TypeScript) + Expo                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  Auth /   │ │  Mapa /  │ │  Chat /  │ │  Perfil /    │   │
│  │  Cadastro │ │  Busca   │ │  Negoc.  │ │  ESG Score   │   │
│  └─────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘   │
│        │            │            │               │           │
│        └────────────┴────────────┴───────────────┘           │
│                         │ HTTPS/WSS                          │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                    API GATEWAY (Nginx)                        │
│                   ┌─────┴──────┐                             │
│              ┌────┤  Uvicorn   ├────┐                        │
│              │    │   (ASGI)   │    │                         │
│              ▼    └────────────┘    ▼                         │
│     ┌──────────────┐      ┌──────────────┐                   │
│     │  Django REST  │      │   Django     │                   │
│     │  Framework    │      │   Channels   │                   │
│     │  (HTTP API)   │      │  (WebSocket) │                   │
│     └──────┬────────┘      └──────┬───────┘                   │
│            │                      │                           │
│     ┌──────┴──────────────────────┴───────┐                   │
│     │           Django ORM                 │                   │
│     │  users/ catalog/ rentals/ payments/  │                   │
│     │       chat/ esg/ notifications/      │                   │
│     └──────┬──────────────┬───────────────┘                   │
│            │              │                                   │
│     ┌──────▼──────┐ ┌────▼─────┐ ┌─────────────┐            │
│     │ PostgreSQL  │ │  Redis   │ │   Celery     │            │
│     │ + PostGIS   │ │ (Cache/  │ │  (Tarefas    │            │
│     │             │ │  Broker) │ │  Assíncronas)│            │
│     └─────────────┘ └──────────┘ └─────────────┘            │
│                                                              │
│     ┌───────────────┐ ┌────────────────┐                     │
│     │ Stripe Connect│ │  AWS S3 / GCS  │                     │
│     │ (Pagamentos)  │ │  (Mídia/Docs)  │                     │
│     └───────────────┘ └────────────────┘                     │
└──────────────────────────────────────────────────────────────┘
```

---

## FASE 1: FUNDAÇÃO BACKEND (Semanas 1-3)
> **Objetivo:** API funcional com modelos, autenticação e busca geoespacial

### Sprint 1.1 — Scaffolding do Projeto Django
- [ ] Criar projeto Django: `aloogai_backend/`
- [ ] Configurar `settings.py` com PostGIS (`django.contrib.gis`)
- [ ] Criar as 7 Django apps: `users`, `catalog`, `rentals`, `payments`, `chat`, `esg`, `notifications`
- [ ] Configurar `.env` com `django-environ`
- [ ] Configurar `.gitignore` (segredos, `.tmp/`, `__pycache__/`, `*.pyc`, `db.sqlite3`)
- [ ] Criar `requirements.txt` / `pyproject.toml`

### Sprint 1.2 — Modelagem de Dados (Django ORM + PostGIS)
- [ ] `users/models.py` — `Usuario` (AbstractUser), `Endereco` (PointField), `DocumentoKYC`
- [ ] `catalog/models.py` — `Categoria`, `Item` (PointField), `FotoItem`
- [ ] `rentals/models.py` — `Locacao` (FSM com status choices), `TimelineLocacao`
- [ ] `payments/models.py` — `TransacaoStripe`, `ContaConectada`
- [ ] `chat/models.py` — `SalaChat`, `Mensagem`
- [ ] `esg/models.py` — `SeloESG`, `HistoricoESG`
- [ ] Gerar e aplicar migrações (`makemigrations` + `migrate`)

### Sprint 1.3 — Autenticação e Usuários
- [ ] Configurar `djangorestframework-simplejwt` (JWT access + refresh)
- [ ] Endpoints: `POST /api/v1/auth/register/`, `POST /api/v1/auth/login/`, `POST /api/v1/auth/refresh/`
- [ ] Serializers + Views para perfil do usuário (`GET/PATCH /api/v1/users/me/`)
- [ ] Fluxo de KYC: upload de documentos, atualização de status

### Sprint 1.4 — Catálogo e Busca Geoespacial
- [ ] CRUD de Itens: `POST/GET/PATCH/DELETE /api/v1/items/`
- [ ] Upload de fotos com resize/compress via Celery
- [ ] **Endpoint de Busca por Proximidade:** `GET /api/v1/items/nearby/?lat=X&lng=Y&raio_km=Z`
  - Usar `ST_DWithin` + `Distance` annotation
  - Ordenação: `is_destacado DESC, distance ASC`
  - Filtros: camada, categoria, preço máximo
- [ ] Serializer GeoJSON com `djangorestframework-gis`
- [ ] Validação por camada:
  - Essential: publicação direta
  - Pro: `aprovado_para_uso=False` até aprovação manual
  - B2B: validação de CNPJ obrigatória

---

## FASE 2: MOTOR FINANCEIRO (Semanas 3-5)
> **Objetivo:** Fluxo completo de caução digital, split e ciclo de locação

### Sprint 2.1 — Integração Stripe Connect
- [ ] Configurar Stripe SDK (`stripe` Python package)
- [ ] Fluxo de onboarding do locador (Connected Account Express)
- [ ] Webhook listener para eventos Stripe (`/api/v1/webhooks/stripe/`)

### Sprint 2.2 — Fluxo da Caução Digital (Escrow)
- [ ] Endpoint: `POST /api/v1/rentals/` — Criar locação + pre-auth Stripe
  - `payment_intents.create(capture_method='manual', amount=diaria+caucao)`
- [ ] Endpoint: `POST /api/v1/rentals/{id}/confirm-delivery/` — Captura parcial (diárias)
  - `payment_intents.capture(amount_to_capture=diarias_liquidas)`
- [ ] Endpoint: `POST /api/v1/rentals/{id}/confirm-return/` — Cancelar auth da caução
  - `payment_intents.cancel(caucao_auth_id)`
- [ ] Endpoint: `POST /api/v1/rentals/{id}/dispute/` — Marcar como CONTESTADO
- [ ] Split automático: Taxa de serviço (10%) + Taxa de sucesso (15%) via `transfer_data`

### Sprint 2.3 — FSM da Locação
- [ ] Implementar máquina de estados com `django-fsm` ou lógica manual
- [ ] Validações de transição (ex: não pode ir de SOLICITADO → ATIVO sem passar por CAUCAO_RETIDA)
- [ ] Timeline de eventos com timestamps (log de auditoria)
- [ ] Celery task: expirar solicitações não confirmadas em 24h

---

## FASE 3: COMUNICAÇÃO EM TEMPO REAL (Semanas 5-6)
> **Objetivo:** Chat funcional entre locador e locatário

### Sprint 3.1 — Django Channels + WebSockets
- [ ] Configurar `channels` + `channels_redis` no Django
- [ ] Configurar Uvicorn como ASGI server
- [ ] Criar `ChatConsumer` (AsyncWebsocketConsumer)
- [ ] Routing: `ws/chat/{locacao_id}/`
- [ ] Autenticação JWT no WebSocket handshake

### Sprint 3.2 — Lógica do Chat
- [ ] Modelo `Mensagem` com criptografia AES-256 no campo de texto
- [ ] Regra: chat só abre quando `Locacao.status >= SOLICITADO`
- [ ] Persistência de mensagens no PostgreSQL
- [ ] Indicadores de leitura (`lida_em` timestamp)
- [ ] API REST fallback: `GET /api/v1/chat/{locacao_id}/messages/` (histórico paginado)

---

## FASE 4: APLICATIVO MOBILE (Semanas 6-10)
> **Objetivo:** App React Native funcional com mapa, cadastro, chat e aluguel

### Sprint 4.1 — Scaffolding React Native
- [ ] Criar projeto com Expo: `npx create-expo-app aloogai-mobile --template`
- [ ] Configurar TypeScript, ESLint, Prettier
- [ ] Estrutura de pastas por feature: `src/features/{auth,map,catalog,rental,chat,profile}/`
- [ ] Configurar navegação: React Navigation (Stack + Bottom Tabs)
- [ ] Setup de estado: TanStack Query (API) + Zustand (UI)

### Sprint 4.2 — Autenticação e Onboarding
- [ ] Telas: Splash, Login, Cadastro (P2P/B2B), Verificação de Telefone
- [ ] Integração JWT: armazenamento seguro (expo-secure-store)
- [ ] Fluxo KYC: câmera para selfie + upload de documento

### Sprint 4.3 — Mapa de Proximidade (Tela Principal)
- [ ] `react-native-maps` com Provider Google
- [ ] Geolocalização ativa: `expo-location` (permissões foreground)
- [ ] Renderização de pins/markers com clustering (`react-native-maps-clustering`)
- [ ] Bottom sheet com detalhes do item ao tocar no pin
- [ ] Filtros: raio, camada, categoria, preço
- [ ] Badge de destaque (Impulsionamento) nos pins

### Sprint 4.4 — Fluxo de Locação
- [ ] Tela de detalhes do item (fotos, descrição, preço, avaliações)
- [ ] Seletor de datas (calendário)
- [ ] Tela de checkout com resumo (diária + caução + taxas)
- [ ] Integração Stripe (React Native SDK para input de cartão)
- [ ] Telas de acompanhamento de status (timeline visual da FSM)

### Sprint 4.5 — Chat in-App
- [ ] Tela de conversas (lista de chats ativos)
- [ ] Tela de mensagens (WebSocket connection)
- [ ] Input de texto + envio de imagens
- [ ] Indicador de "digitando..." + status de leitura
- [ ] Push notifications para novas mensagens

### Sprint 4.6 — Perfil e ESG
- [ ] Tela de perfil (dados, itens cadastrados, avaliações)
- [ ] Score ESG com visualização de CO₂ economizado
- [ ] Selos ecológicos desbloqueáveis
- [ ] Tela "Meus Aluguéis" (como locador e locatário)

---

## FASE 5: MÓDULO ESG (Semana 10-11)
> **Objetivo:** Cálculo de pegada de carbono e gamificação

### Sprint 5.1 — Motor de Cálculo ESG
- [ ] Signal `post_save` em `Locacao` (quando status → CONCLUIDO)
- [ ] Tabela de referência: `FatorESGCategoria` (CO₂ por tipo de item)
- [ ] Fórmula: `co2 = custo_fabricacao * fator_reuso + reducao_frete`
- [ ] Incrementar `Usuario.score_esg`
- [ ] Celery task para recalcular rankings periódicos

### Sprint 5.2 — Selos e Gamificação
- [ ] Selos: "Vizinho Verde" (10 locações), "Herói Circular" (50), "Embaixador ESG" (100)
- [ ] Badge visual no perfil público
- [ ] Notificação push ao desbloquear selo

---

## FASE 6: POLISH, TESTES E DEPLOY (Semanas 11-14)
> **Protocolo VLAEGS: Fases E (Estilo), G (Gatilho), S (Segurança)**

### Sprint 6.1 — Estilo (E)
- [ ] Design system completo (cores, tipografia, espaçamento)
- [ ] Animações e micro-interações (Reanimated)
- [ ] Dark mode
- [ ] Feedback visual para todas as ações (loading, success, error states)
- [ ] Teste de UX com 3-5 usuários reais

### Sprint 6.2 — Testes e QA
- [ ] Testes unitários backend: `pytest` + `factory_boy`
- [ ] Testes de integração: fluxo completo de locação (API)
- [ ] Testes E2E mobile: Detox ou Maestro
- [ ] Cobertura mínima: 80% backend

### Sprint 6.3 — Gatilho (G) — Deploy
- [ ] Backend → Railway (PostgreSQL+PostGIS, Redis, Uvicorn)
- [ ] CI/CD: GitHub Actions (lint, test, deploy)
- [ ] Mobile → Build com EAS Build (Expo Application Services)
- [ ] Submissão: Google Play Store + Apple App Store
- [ ] Monitoramento: Sentry (erros) + PostHog (analytics)

### Sprint 6.4 — Segurança (S) — Auditoria Final
- [ ] Varredura de segredos hardcoded (`.env` audit)
- [ ] Validação de inputs (XSS/SQLi prevention)
- [ ] Rate limiting nos endpoints sensíveis
- [ ] HTTPS obrigatório (SSL/TLS)
- [ ] `.gitignore` verificado (`.env`, `.tmp/`, `node_modules/`, `*.pyc`)
- [ ] Tratamento de falhas gracioso (sem stack traces expostos)
- [ ] LGPD compliance check (dados pessoais, consentimento)

---

## Resumo de Entregas por Fase

| Fase | Entrega | Semanas | Dependência |
|---|---|---|---|
| **1. Fundação Backend** | API REST com auth, modelos e busca geoespacial | 1-3 | — |
| **2. Motor Financeiro** | Caução digital, split, FSM de locação | 3-5 | Fase 1 |
| **3. Chat Real-Time** | WebSocket chat entre locador/locatário | 5-6 | Fase 1 |
| **4. App Mobile** | App funcional com mapa, aluguel e chat | 6-10 | Fases 1-3 |
| **5. Módulo ESG** | Cálculo CO₂, selos, gamificação | 10-11 | Fase 2 |
| **6. Deploy** | Lojas, CI/CD, segurança, monitoramento | 11-14 | Todas |

---

> ⚠️ **BLOQUEIO DO PROTOCOLO V.L.A.E.G.S.:**
> Nenhum código será escrito em `tools/` ou nos diretórios do projeto até que este Blueprint seja **aprovado pelo usuário**.
> Responda com **"APROVADO"** para iniciar a Fase 1, Sprint 1.1.
