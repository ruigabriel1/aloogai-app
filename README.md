<div align="center">
  <img src="logo.jpeg" alt="Logo do Aloogaí" width="160" height="160">
  <h1>Aloogaí</h1>
  <p><b>Aluguel de objetos entre vizinhos: ache por perto, alugue com caução no cartão e converse em tempo real.</b></p>

  ![CI](https://github.com/ruigabriel1/aloogai-app/actions/workflows/ci.yml/badge.svg)
  ![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django)
  ![React Native](https://img.shields.io/badge/React_Native-Expo_54-20232A?logo=react)
  ![PostGIS](https://img.shields.io/badge/PostGIS-busca_por_raio-336791?logo=postgresql&logoColor=white)
  ![Stripe](https://img.shields.io/badge/Stripe-modo_teste-626CD9?logo=stripe&logoColor=white)
</div>

---

## O que é

Marketplace de locação por proximidade (P2P e lojistas). Quem tem uma furadeira parada anuncia;
quem precisa dela por dois dias encontra no mapa, aluga e devolve. O valor do aluguel só é cobrado
quando a locação termina, e a caução fica apenas **autorizada** no cartão até a devolução.

É um projeto de portfólio: o objetivo é um **MVP que funciona de ponta a ponta**, não um produto publicado.

## O que funciona (e está testado)

| Fluxo | Como funciona |
|---|---|
| Cadastro e login | JWT por e-mail; o app guarda os tokens no SecureStore e renova o access token sozinho (refresh rotacionado com blacklist) |
| Anunciar item | Item com foto (upload multipart), categoria e localização; itens da camada **PRO** só aparecem depois de aprovados no admin |
| Achar por perto | `GET /catalog/itens/proximos/?lat&lng&raio_km` com `ST_DWithin` no PostGIS (no SQLite de dev, a distância é calculada em Python) |
| Alugar | O backend cria um **PaymentIntent com captura manual** (diárias + taxa + caução) e o app confirma com a **PaymentSheet** do Stripe |
| Entregar → devolver → concluir | Máquina de estados (`django-fsm`); ao concluir, captura **só o devido** e o Stripe libera a caução na mesma operação |
| Chat | WebSocket (Django Channels) autenticado por JWT, com histórico cifrado em repouso (Fernet) e fallback REST |
| Impacto ambiental | CO₂ evitado por locação e selos ESG calculados ao concluir |

**Números:** 110 testes no backend (API, permissões, WebSocket, fluxo de pagamento com Stripe mockado)
e o app compila sem erros de TypeScript. A CI roda tudo a cada push e confere as migrações num PostGIS de verdade.

## Arquitetura

```
App (Expo / React Native)                     Backend (Django 6 + DRF, ASGI)
  React Query + Zustand  ── HTTPS/JWT ──►      /api/v1/  catalog · rentals · payments · chat · esg · users
  PaymentSheet (Stripe)                         Channels  /ws/chat/<locacao>/?token=…
  WebSocket do chat      ── WS/JWT ────►        Celery    expira solicitações sem pagamento (beat, a cada hora)
                                                    │
                          PostgreSQL + PostGIS ◄────┤──► Redis (channel layer, broker, cache)
                                                    └──► Stripe (PaymentIntent manual, Connect opcional)
```

Decisões que valem a explicação:

- **Um PaymentIntent, captura parcial.** Autoriza diárias + taxa + caução; na conclusão captura só diárias + taxa.
  O restante (a caução) é liberado pelo próprio Stripe. Assim não existe "capturar e depois cancelar".
- **Valores numa fonte só.** `LocacaoService` calcula diárias e taxas (lidas do settings), grava na locação, e o
  pagamento usa esses valores. Não há uma segunda conta paralela.
- **Mesmas migrações para SQLite e PostGIS.** O `PointField` de `apps/core/geo_compat.py` se descreve igual
  nos dois modos; a CI verifica com `makemigrations --check` contra um PostGIS.
- **Permissões por dono.** Editar ou apagar item de outra pessoa devolve 404 (não revela que existe);
  avaliação só do locatário e só de locação concluída.

## Como rodar

### Backend (Docker)

```bash
cp .env.example .env        # coloque as chaves de TESTE do Stripe (sk_test_..., pk_test_...)
docker compose up --build   # PostGIS + Redis + API + Celery em http://localhost:8000
docker compose exec api python manage.py createsuperuser
docker compose exec api python manage.py seed_fake_data   # opcional: itens de exemplo
```

### Backend (sem Docker, SQLite)

```bash
cd backend
python -m venv venv && venv/Scripts/activate      # Linux/Mac: source venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env                               # precisa de DJANGO_SECRET_KEY
python manage.py migrate && python manage.py seed_selos
python manage.py runserver 0.0.0.0:8000
python -m pytest                                   # testes
```

### App (Expo Go)

```bash
cd mobile
cp .env.example .env    # EXPO_PUBLIC_API_URL=http://SEU_IP_NA_REDE:8000 e a pk_test do Stripe
npm install
npx expo start          # abra no Expo Go pelo QR code
```

No celular físico, a API precisa estar acessível pelo IP do computador na rede (não `localhost`).
Para pagar, use o cartão de teste do Stripe `4242 4242 4242 4242`, qualquer data futura e qualquer CVC.

## Limitações conhecidas

- **Contestação sem mediação:** uma locação contestada não tem fluxo de resolução nem captura da caução.
- **KYC manual:** documentos são enviados, mas a aprovação é pelo admin e não bloqueia ações.
- **Push e e-mail:** notificações ficam no banco; não há envio por FCM.
- **Datas digitadas** no checkout (AAAA-MM-DD), sem calendário.
- O app ainda não tem testes automatizados nem lint; a garantia hoje é o TypeScript estrito e o bundle de build.
- O ambiente Docker foi escrito e validado em sintaxe, mas a CI é quem roda o PostGIS de verdade.

## Stack

**Backend:** Python 3.12, Django 6, Django REST Framework, SimpleJWT, Django Channels, Celery, PostgreSQL/PostGIS,
Redis, Stripe, django-fsm, pytest.
**App:** React Native (Expo SDK 54), TypeScript, React Navigation, TanStack Query, Zustand, react-native-maps,
@stripe/stripe-react-native.
