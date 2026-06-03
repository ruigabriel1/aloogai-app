# 🔍 findings.md — Pesquisas e Descobertas

> **Projeto:** Aloogaí | **Protocolo:** V.L.A.E.G.S.

---

## Descoberta 1: Framework Mobile — React Native vs Flutter (2026-06-01)

**Decisão:** React Native (TypeScript) com Expo

**Justificativa:**
- Pool de desenvolvedores JS/TS no Brasil é significativamente maior que Dart
- `react-native-maps` é maduro e battle-tested para marketplace com pins/clustering
- OTA updates via CodePush permitem iteração rápida sem resubmissão às lojas
- Componentes nativos da plataforma (melhor UX transacional)
- Código React reutilizável se houver painel web admin no futuro

**Riscos Mapeados:**
- Expo Go não suporta módulos nativos customizados (exige build dev-client para funcionalidades avançadas de câmera/maps)
- Performance de listas longas exige FlatList virtualizada + memo cuidadoso

---

## Descoberta 2: Gateway de Pagamento — Stripe Connect (2026-06-01)

**Decisão:** Stripe Connect (confirmado pelo usuário)

**Capacidades Confirmadas:**
- ✅ Split de Pagamentos — via Connected Accounts (Standard ou Express)
- ✅ Pre-Authorization (Caução) — `payment_intents` com `capture_method: manual`
- ✅ Captura parcial e cancelamento de auth
- ✅ KYC via Identity Verification API
- ✅ Sandbox robusto para testes

**Limitações Críticas:**
- ⚠️ Pre-autorizações expiram em **7 dias** (padrão da bandeira). Para locações > 7 dias, será necessário renovar a pre-auth ou adotar estratégia diferente
- ⚠️ Pix no Brasil via Stripe requer habilitação especial (solicitar ao onboarding)
- ⚠️ Taxas: 3.99% + R$ 0.39 por transação com cartão brasileiro

**Fluxo Técnico da Caução:**
```
1. POST /v1/payment_intents (capture_method: manual, amount: diaria + caucao)
2. Confirmar entrega → POST /v1/payment_intents/{id}/capture (amount_to_capture: diaria)
3. Devolução OK → POST /v1/payment_intents/{id_caucao}/cancel
3. Sinistro → Mediação → POST /v1/payment_intents/{id_caucao}/capture
```

---

## Descoberta 3: Deploy para MVP — Railway (2026-06-01)

**Decisão:** Railway para MVP, GCP Cloud Run para escala

**Railway suporta:**
- PostgreSQL gerenciado (PostGIS habilitável via extensão)
- Redis gerenciado
- Deploy por Git push
- Custo estimado MVP: ~$10-25/mês

**Migração futura:**
- GCP Cloud Run com Cloud SQL (PostGIS) + Memorystore (Redis)
- Docker container + CI/CD via GitHub Actions

---

## Descoberta 4: Real-Time Chat — Django Channels (2026-06-01)

**Stack:** Django Channels + Redis + Uvicorn (ASGI)

**Práticas Adotadas:**
- Usar `AsyncWebsocketConsumer` com `database_sync_to_async` para ORM
- Heartbeat/ping-pong para detectar conexões mortas
- Criptografia de mensagens no banco (AES-256) — MVP simplificado antes de E2E completo
- Escalabilidade: até ~1000 conexões simultâneas. Se ultrapassar, migrar para Centrifugo

---

## Descoberta 5: Projetos Open Source de Referência (2026-06-01)

| Projeto | Relevância para Aloogaí |
|---|---|
| **Saleor** (Django, 22.9k ⭐) | Arquitetura modular Django, sistema de permissões |
| **ThriftHub** (React Native + Django) | Referência direta — multi-vendor com Expo |
| **Rocket.Chat RN** (React Native) | Arquitetura de chat em alta performance |

**Padrões Adotados dessas Referências:**
- Django apps modulares por domínio (`users/`, `catalog/`, `rentals/`, etc.)
- React Native organizado por features (`src/features/auth/`, `src/features/map/`)
- State management: TanStack Query (API cache) + Zustand (UI state)
