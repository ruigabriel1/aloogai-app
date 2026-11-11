/**
 * API de Locações do Aloogaí
 *
 * Funções para gerenciar o ciclo de vida das locações:
 * criar, listar, obter detalhes e cancelar.
 * Endpoints: /rentals/
 */

import { apiClient } from './client';

// ─── Tipos ──────────────────────────────────────────────

/** Status FSM da locação (transições unidirecionais) */
export type StatusLocacao =
  | 'SOLICITADO'
  | 'CAUCAO_RETIDA'
  | 'ATIVO'
  | 'DEVOLVIDO'
  | 'CONCLUIDO'
  | 'CANCELADO'
  | 'CONTESTADO';

/** Evento na timeline da locação */
export interface TimelineEvento {
  status: StatusLocacao;
  timestamp: string;
  observacao?: string;
}

/** Item resumido dentro da locação */
export interface ItemLocacao {
  id: string;
  titulo: string;
  foto_capa_url: string;
  preco_diaria: string;
  locador: {
    id: string;
    nome: string;
    foto_perfil?: string;
  };
}

/** Locação completa */
export interface Locacao {
  id: string;
  status: StatusLocacao;
  item: ItemLocacao;
  locatario: {
    id: string;
    nome: string;
    foto_perfil?: string;
  };
  data_inicio: string;
  data_fim: string;
  valor_diarias: string;
  valor_caucao: string;
  taxa_servico: string;
  valor_total: string;
  payment_intent_id?: string;
  caucao_auth_id?: string;
  co2_evitado: number;
  timeline: TimelineEvento[];
  sala_chat_id?: string;
  criado_em: string;
  atualizado_em: string;
}

/** Payload para criar locação */
export interface CriarLocacaoPayload {
  item_id: string;
  data_inicio: string;
  data_fim: string;
  payment_method_id?: string;
}

/** Resposta paginada de locações */
export interface LocacoesResponse {
  results: Locacao[];
  count: number;
  next: string | null;
  previous: string | null;
}

// ─── Funções da API ─────────────────────────────────────

/**
 * Cria uma nova solicitação de locação.
 *
 * POST /rentals/locacoes/
 */
export async function criarLocacao(
  payload: CriarLocacaoPayload,
): Promise<Locacao> {
  const response = await apiClient.post<Locacao>('rentals/locacoes/', payload);
  return response.data;
}

/**
 * Lista as locações do usuário autenticado.
 *
 * GET /rentals/locacoes/
 * @param tipo - 'locatario' ou 'locador' para filtrar por papel
 */
export async function listarLocacoes(
  tipo?: 'locatario' | 'locador',
): Promise<Locacao[]> {
  const params: Record<string, string> = {};
  if (tipo) params.tipo = tipo;

  const response = await apiClient.get<LocacoesResponse>('rentals/locacoes/', {
    params,
  });
  return response.data.results;
}

/**
 * Obtém detalhes de uma locação específica.
 *
 * GET /rentals/locacoes/{id}/
 */
export async function obterLocacao(id: string): Promise<Locacao> {
  const response = await apiClient.get<Locacao>(`rentals/locacoes/${id}/`);
  return response.data;
}

/**
 * Cancela uma locação (somente antes de CAUCAO_RETIDA).
 *
 * POST /rentals/locacoes/{id}/cancelar/
 */
export async function cancelarLocacao(id: string): Promise<Locacao> {
  const response = await apiClient.post<Locacao>(
    `rentals/locacoes/${id}/cancelar/`,
  );
  return response.data;
}

/** Re-export por conveniência */
export const rentalsApi = {
  criarLocacao,
  listarLocacoes,
  obterLocacao,
  cancelarLocacao,
};

export default rentalsApi;
