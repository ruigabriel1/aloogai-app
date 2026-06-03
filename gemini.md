# 📜 gemini.md — Constituição do Projeto Aloogaí
> **Status:** INICIALIZADO | **Versão:** 0.1.0 | **Data:** 2026-06-01
> **Protocolo:** V.L.A.E.G.S. | **Fase Atual:** V (Visão)

---

## 1. Identidade do Projeto

| Campo | Valor |
|---|---|
| **Nome** | Aloogaí |
| **Slogan** | "A vizinhança é seu estoque. Alugue e economize." |
| **Tipo** | Marketplace P2P/B2B de Locação por Proximidade |
| **Modelo** | Economia Circular — Locação de Itens Ociosos |
| **Estrela Guia (MVP)** | App publicado nas lojas (Play Store / App Store) com cadastro, mapa e chat funcional |

---

## 2. Stack Tecnológico (Decisões Travadas)

| Camada | Tecnologia | Justificativa |
|---|---|---|
| **Mobile (Frontend)** | React Native (TypeScript) + Expo | Maior ecossistema JS/TS no Brasil, `react-native-maps` maduro, OTA updates via CodePush |
| **Backend (API Core)** | Python 3.11+ / Django 5.x + Django REST Framework | Robusto, maduro, comunidade sólida |
| **Banco de Dados** | PostgreSQL 16 + PostGIS 3.4 | Consultas espaciais nativas (`ST_DWithin`), índices GiST |
| **Cache / Fila** | Redis 7 | Channel layer (WebSockets), cache, Celery broker |
| **Real-Time Chat** | Django Channels + Uvicorn (ASGI) | Chat de negociação direta, integrado ao Django ORM |
| **Pagamentos** | Stripe Connect | Split de pagamentos, pre-auth (caução digital), KYC, sandbox robusto |
| **Deploy (MVP)** | Railway | Deploy rápido, Postgres/Redis gerenciados, Git integration |
| **Deploy (Escala)** | GCP Cloud Run + Cloud SQL + Memorystore | Auto-scaling, containerizado |
| **Armazenamento** | AWS S3 ou GCS | Fotos de itens, documentos KYC |

---

## 3. Esquema de Dados (Fonte da Verdade)

### 3.1. Entidades Principais

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Usuario   │────▶│   Endereco   │     │   Categoria  │
│  (AbstractU)│     │ (PointField) │     │              │
└──────┬──────┘     └──────────────┘     └──────┬───────┘
       │                                        │
       │ locador                                │
       ▼                                        ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│     Item     │────▶│  FotoItem    │     │   Avaliacao  │
│ (PointField) │     │              │     │              │
└──────┬───────┘     └──────────────┘     └──────────────┘
       │
       │ item
       ▼
┌──────────────┐     ┌──────────────┐
│   Locacao    │────▶│  Mensagem    │
│ (Ciclo FSM)  │     │ (WebSocket)  │
└──────────────┘     └──────────────┘
```

### 3.2. JSON Schemas — Payloads da API

#### Entrada: Busca por Proximidade
```json
{
  "lat": -23.5505,
  "lng": -46.6333,
  "raio_km": 5,
  "camada": "ESSENTIAL|PRO|B2B|null",
  "categoria_id": "uuid|null",
  "preco_max": 150.00,
  "ordenar_por": "distancia|preco|avaliacao",
  "page": 1,
  "page_size": 20
}
```

#### Saída: Item no Mapa (GeoJSON)
```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [-46.6333, -23.5505]
  },
  "properties": {
    "id": "uuid",
    "titulo": "Furadeira Bosch Professional",
    "camada": "ESSENTIAL",
    "preco_diaria": "25.00",
    "valor_caucao": "150.00",
    "distancia_km": 1.2,
    "is_destacado": true,
    "avaliacao_media": 4.7,
    "foto_capa_url": "https://...",
    "locador": {
      "id": "uuid",
      "nome": "João S.",
      "score_esg": 42.5,
      "avaliacao_media": 4.8
    }
  }
}
```

#### Entrada: Criar Locação
```json
{
  "item_id": "uuid",
  "data_inicio": "2026-06-10",
  "data_fim": "2026-06-12",
  "payment_method_id": "pm_stripe_xxx"
}
```

#### Saída: Status da Locação (FSM)
```json
{
  "id": "uuid",
  "status": "CAUCAO_RETIDA",
  "item": { "titulo": "...", "locador": "..." },
  "valor_diarias": "50.00",
  "valor_caucao": "150.00",
  "payment_intent_id": "pi_xxx",
  "caucao_auth_id": "pi_caucao_xxx",
  "co2_evitado": 0.0,
  "timeline": [
    {"status": "SOLICITADO", "timestamp": "2026-06-10T10:00:00Z"},
    {"status": "CAUCAO_RETIDA", "timestamp": "2026-06-10T10:01:30Z"}
  ]
}
```

---

## 4. Regras Comportamentais (Invariantes)

> Estas regras NUNCA podem ser violadas pelo código. Se uma mudança exigir alteração, este documento deve ser atualizado PRIMEIRO.

1. **Idioma:** App 100% em pt-BR. Internacionalização prevista para futuro (i18n-ready), mas não implementada no MVP.
2. **Camada Pro — Aprovação Obrigatória:** Itens da Camada Pro (`requer_licenca=True`) **NÃO aparecem no mapa** até `aprovado_para_uso=True` ser setado manualmente por um admin.
3. **Chat Condicionado:** O chat entre locador e locatário **só é habilitado APÓS** uma solicitação de locação (`Locacao.status >= SOLICITADO`).
4. **Caução Intocável:** A caução digital (pre-auth) **NUNCA é capturada automaticamente**. Só pode ser cobrada com mediação humana em caso de sinistro (`status=CONTESTADO`).
5. **Split Transparente:** Toda transação de diária aplica as taxas:
   - **Taxa de Serviço Locatário:** 10% sobre valor da diária (pago pelo locatário)
   - **Taxa de Sucesso Locador:** 15% sobre valor recebido (retido pelo Aloogaí no split)
6. **KYC Progressivo:** 
   - P2P Essential: CPF + selfie (verificação simplificada)
   - P2P Pro: CPF + selfie + documento de licença do item
   - B2B: CNPJ + contrato social + selfie do responsável
7. **FSM Estrita da Locação:** As transições de status são unidirecionais:
   ```
   SOLICITADO → CAUCAO_RETIDA → ATIVO → DEVOLVIDO → CONCLUIDO
                                    ↘ CONTESTADO (de qualquer estado ativo)
   SOLICITADO → CANCELADO (somente antes de CAUCAO_RETIDA)
   ```

---

## 5. Invariantes Arquiteturais

1. **Dados Geoespaciais:** Sempre SRID 4326 (WGS84). Usar `geography=True` nos PointFields. Busca por raio via `ST_DWithin` + índice GiST.
2. **API RESTful:** Versionada (`/api/v1/`). Autenticação JWT (access + refresh tokens).
3. **Separação de Django Apps:**
   - `users/` — Cadastro, KYC, perfil, autenticação
   - `catalog/` — Itens, categorias, fotos, busca geoespacial
   - `rentals/` — Locações, FSM, ciclo de vida
   - `payments/` — Integração Stripe, split, caução
   - `chat/` — Django Channels, mensagens, WebSocket consumers
   - `esg/` — Score ESG, cálculo CO₂, selos
   - `notifications/` — Push notifications, e-mail
4. **Variáveis de Ambiente:** Todas as chaves/segredos em `.env`. Zero hardcoded.
5. **Arquivos Temporários:** Sempre em `.tmp/`. Nunca commitados.

---

## 6. Log de Manutenção

| Data | Alteração | Autor |
|---|---|---|
| 2026-06-01 | Inicialização do gemini.md — Stack, schemas, regras comportamentais definidas | Sistema |
