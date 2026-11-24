/**
 * API de Locações do Aloogaí
 *
 * Os tipos espelham backend/apps/rentals/serializers.py.
 */

import { apiClient } from './client';
import type { Paginado } from './catalog';

// ─── Tipos ──────────────────────────────────────────────

export type StatusLocacao =
  | 'SOLICITADO'
  | 'CAUCAO_RETIDA'
  | 'ATIVO'
  | 'DEVOLVIDO'
  | 'CONCLUIDO'
  | 'CANCELADO'
  | 'CONTESTADO';

/** LocacaoListSerializer */
export interface LocacaoResumo {
  id: string;
  item: string;
  item_titulo: string;
  item_foto_url: string | null;
  locador_nome: string;
  locatario_nome: string;
  /** Papel de quem está vendo a lista */
  papel: 'locador' | 'locatario';
  status: StatusLocacao;
  status_display: string;
  data_inicio: string;
  data_fim: string;
  numero_diarias: number;
  total_locatario: string;
  created_at: string;
}

/** TimelineLocacaoSerializer */
export interface EventoTimeline {
  id: string;
  status_anterior: StatusLocacao | '';
  status_novo: StatusLocacao;
  observacao: string;
  created_at: string;
}

/** LocacaoDetailSerializer */
export interface LocacaoDetalhe {
  id: string;
  item: string;
  item_titulo: string;
  locatario: string;
  locatario_nome: string;
  locador_nome: string;
  status: StatusLocacao;
  status_display: string;
  data_inicio: string;
  data_fim: string;
  numero_diarias: number;
  valor_diarias: string;
  valor_caucao: string;
  valor_taxa_servico: string;
  valor_taxa_sucesso: string;
  total_locatario: string;
  co2_evitado: number | null;
  timeline: EventoTimeline[];
  created_at: string;
  updated_at: string;
}

/** Payload de POST rentals/locacoes/ (LocacaoCreateSerializer) */
export interface CriarLocacaoPayload {
  item: string;
  data_inicio: string;
  data_fim: string;
}

/** Resposta da criação: a locação + dados para a PaymentSheet do Stripe */
export interface LocacaoCriada extends LocacaoDetalhe {
  pagamento?: {
    client_secret: string;
    payment_intent_id: string;
  } | null;
}

// ─── Funções da API ─────────────────────────────────────

/** POST rentals/locacoes/ */
export async function criarLocacao(payload: CriarLocacaoPayload): Promise<LocacaoCriada> {
  const response = await apiClient.post<LocacaoCriada>('rentals/locacoes/', payload);
  return response.data;
}

/** GET rentals/locacoes/?tipo=locatario|locador */
export async function listarLocacoes(tipo?: 'locatario' | 'locador'): Promise<LocacaoResumo[]> {
  const params: Record<string, string> = {};
  if (tipo) params.tipo = tipo;
  const response = await apiClient.get<Paginado<LocacaoResumo>>('rentals/locacoes/', { params });
  return response.data.results;
}

/** GET rentals/locacoes/{id}/ */
export async function obterLocacao(id: string): Promise<LocacaoDetalhe> {
  const response = await apiClient.get<LocacaoDetalhe>(`rentals/locacoes/${id}/`);
  return response.data;
}

/** POST rentals/locacoes/{id}/{acao}/ — transições da máquina de estados */
export type AcaoLocacao =
  | 'confirmar-entrega'
  | 'confirmar-devolucao'
  | 'concluir'
  | 'cancelar';

export async function executarAcao(id: string, acao: AcaoLocacao): Promise<LocacaoDetalhe> {
  const response = await apiClient.post<LocacaoDetalhe>(`rentals/locacoes/${id}/${acao}/`);
  return response.data;
}

/**
 * POST rentals/locacoes/{id}/confirmar-pagamento/ — o backend consulta o Stripe.
 * Logo após a PaymentSheet o Stripe pode levar um instante: tenta de novo uma vez.
 */
export async function confirmarPagamento(id: string): Promise<LocacaoDetalhe> {
  try {
    const response = await apiClient.post<LocacaoDetalhe>(`rentals/locacoes/${id}/confirmar-pagamento/`);
    return response.data;
  } catch (error) {
    const status = (error as { response?: { status?: number } })?.response?.status;
    if (status !== 409) throw error;
    await new Promise((resolve) => setTimeout(resolve, 1500));
    const response = await apiClient.post<LocacaoDetalhe>(`rentals/locacoes/${id}/confirmar-pagamento/`);
    return response.data;
  }
}

export const rentalsApi = {
  criarLocacao,
  listarLocacoes,
  obterLocacao,
  executarAcao,
  confirmarPagamento,
};

export default rentalsApi;
