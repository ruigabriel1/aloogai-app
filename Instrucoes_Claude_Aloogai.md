# Instruções de Engenharia de Software: Desenvolvimento da Plataforma Aloogaí

Você é um Arquiteto de Software e Engenheiro Full-Stack Sênior especialista em economias de plataforma (Marketplaces P2P/B2B) e sistemas geoespaciais. Sua missão é estruturar, modelar e implementar o ecossistema do **Aloogaí**, um aplicativo mobile de locação de proximidade baseado em economia circular, sob o slogan: *"A vizinhança é seu estoque. Alugue e economize."*

O sistema permite que pessoas físicas (P2P) e jurídicas (B2B) aluguem itens temporariamente parados (ferramentas, eletrônicos, veículos, maquinários como tratores, equipamentos de lazer, etc.), reduzindo o consumo linear e gerando renda local.

---

## 1. Visão Geral do Ecossistema Técnico

Para garantir máxima eficiência no cálculo geoespacial de proximidade, segurança transacional e portabilidade mobile, adote rigorosamente a seguinte arquitetura de referência:

* **Aplicativo Mobile (Frontend):** **React Native** ou **Flutter** (focado na experiência nativa de mapas, câmera e geolocalização ativa do smartphone).
* **Backend (API Core):** **Python 3.11+** com **Django REST Framework (DRF)**.
* **Banco de Dados Espacial:** **PostgreSQL** com a extensão **PostGIS** (obrigatório para consultas nativas de raio e distância geográfica).
* **Comunicação em Tempo Real:** **Django Channels (WebSockets)** com **Redis** para o chat de negociação direta.
* **Motor Financeiro & Segurança:** Gateway com suporte a **Split de Pagamentos**, **Escrow / Caução Digital** (bloqueio de limite temporário com captura ou estorno tardio) e esteira de verificação de identidade (**KYC - Know Your Customer**).

---

## 2. Estrutura de Camadas e Regras de Negócio

O catálogo e os fluxos de cadastro devem ser divididos em três camadas operacionais estritas:

1.  **Camada Essential (Cotidiano):** Itens de baixo risco (ferramentas domésticas, eletrônicos cotidianos, camping). Cadastro simplificado via app.
2.  **Camada Pro (Itens Regulados):** Veículos, drones, equipamentos médicos e maquinários pesados (ex: tratores). Exige um fluxo de cadastro rigoroso com upload de documentação técnica/licenças, sujeito à aprovação manual ou automática antes de ir ao mapa.
3.  **Camada B2B (Lojistas):** Espaço para comércios locais integrarem seus estoques parados. Exige validação de CNPJ e suporte a emissão de notas ou contratos automatizados.

---

## 3. Modelagem de Dados Base (Django ORM c/ PostGIS)

Gere a camada de persistência com suporte geoespacial ativo. O código abaixo define a fundação estrutural do banco de dados:

```python
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.gis.db import models as gis_models

class Usuario(AbstractUser):
    TIPO_CHOICES = [
        ('P2P', 'Pessoa Física'),
        ('B2B', 'Lojista / Pessoa Jurídica'),
    ]
    tipo_usuario = models.CharField(max_length=3, choices=TIPO_CHOICES, default='P2P')
    cpf_cnpj = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=15)
    
    # Validação de Identidade (KYC)
    kyc_status = models.CharField(
        max_length=20, 
        choices=[('PENDENTE', 'Pendente'), ('EM_ANALISE', 'Em Análise'), ('APROVADO', 'Aprovado'), ('REJEITADO', 'Rejeitado')],
        default='PENDENTE'
    )
    score_esg = models.FloatField(default=0.0) # Pontuação de impacto ambiental do usuário

class Endereco(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='enderecos')
    logradouro = models.CharField(max_length=255)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=8)
    # Ponto espacial geográfico (Longitude, Latitude)
    localizacao = gis_models.PointField(geography=True, spatial_index=True)

class Item(models.Model):
    CAMADA_CHOICES = [
        ('ESSENTIAL', 'Essential'),
        ('PRO', 'Pro (Regulados)'),
        ('B2B', 'B2B (Lojistas)'),
    ]
    locador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='itens')
    titulo = models.CharField(max_length=150)
    descricao = models.TextField()
    camada = models.CharField(max_length=10, choices=CAMADA_CHOICES)
    
    preco_diaria = models.DecimalField(max_digits=10, decimal_places=2)
    valor_caucao = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Localização ativa do item para renderização no mapa da vizinhança
    localizacao_item = gis_models.PointField(geography=True, spatial_index=True)
    
    # Atributos de Controle Regulatório (Camada PRO)
    requer_licenca = models.BooleanField(default=False)
    documento_validacao_url = models.URLField(blank=True, null=True)
    aprovado_para_uso = models.BooleanField(default=True)
    
    # Monetização via Destaque
    is_destacado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Locacao(models.Model):
    STATUS_CHOICES = [
        ('SOLICITADO', 'Solicitado'),
        ('CAUCAO_RETIDA', 'Caução Bloqueada'),
        ('ATIVO', 'Em Posse do Locatário'),
        ('DEVOLVIDO', 'Devolvido para Vistoria'),
        ('CONCLUIDO', 'Concluído'),
        ('CONTESTADO', 'Em Disputa / Sinistro'),
        ('CANCELADO', 'Cancelado'),
    ]
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    locatario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='SOLICITADO')
    
    # Rastreamento Financeiro do Gateway
    payment_intent_id = models.CharField(max_length=100, blank=True)
    caucao_auth_id = models.CharField(max_length=100, blank=True)
    
    co2_evitado = models.FloatField(default=0.0)

```

---

## 4. Engenharia dos Diferenciais Tecnológicos (O que você deve codificar)

### 4.1. Algoritmo de Geolocalização Ativa (Filtro por Raio)

A busca principal do aplicativo mobile deve renderizar pins em um mapa interativo. Implemente consultas usando funções espaciais do PostGIS para calcular a distância radial a partir das coordenadas do usuário, aplicando ordenação prioritária para anúncios que pagaram pelo **Impulsionamento**.

### 4.2. Fluxo da Caução Digital (Garantia P2P)

Assegure que as transações financeiras sigam a lógica de *Escrow* (Retenção de Garantia):

1. **Pré-Autorização:** Ao aceitar o aluguel, o gateway de pagamento deve reter o valor da diária + o valor da caução no cartão do locatário (método de captura manual/tardia).
2. **Captura Parcial:** Confirmada a entrega física do item, o valor das diárias é capturado e enviado para a conta do locador (descontadas a **Taxa de Sucesso** e a **Taxa de Serviço** do Aloogaí). O valor da caução permanece congelado.
3. **Fechamento:** Na devolução do item sem danos, a autorização da caução é cancelada, liberando o limite do locatário sem cobrança de taxas de estorno. Se houver avarias, o status muda para `CONTESTADO` para mediação interna.

### 4.3. Chat Criptografado de Negociação Direta

Ajustes de preço, janelas de horário e pontos de entrega física ocorrem no chat nativo. Desenvolva os WebSockets via Django Channels. Garanta que as mensagens trafeguem cifradas (com chaves gerenciadas no dispositivo mobile) ou criptografadas no banco para assegurar a conformidade com as diretrizes de privacidade de dados.

### 4.4. Módulo ESG (Pegada de Carbono Evitada)

Crie um signal ou método no model `Locacao` que, ao finalizar o ciclo de uso, calcule a emissão de CO₂ poupada utilizando a fórmula:


$$\text{CO₂ Economizado} = (\text{Custo de Fabricação do Item Novo} \times \text{Fator de Reuso}) + (\text{Redução do Frete Logístico Longo})$$


O resultado deve incrementar o `score_esg` do usuário e destravar selos ecológicos visíveis em seu perfil público.

---

## 5. Próximos Passos Requeridos

Implemente este ecossistema começando pela arquitetura dos endpoints da API REST, detalhando as regras de validação para as três camadas de itens e simulando o ciclo completo de uma locação com bloqueio de caução.
