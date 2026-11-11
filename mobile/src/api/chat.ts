/**
 * API de Chat do Aloogaí
 *
 * Funções para gerenciar salas de chat e mensagens.
 * O chat é habilitado somente após uma solicitação de locação.
 * Endpoints: /chat/
 */

import { apiClient } from './client';

// ─── Tipos ──────────────────────────────────────────────

/** Participante da sala de chat */
export interface Participante {
  id: string;
  nome: string;
  foto_perfil?: string;
}

/** Resumo do item vinculado à sala */
export interface ItemSala {
  id: string;
  titulo: string;
  foto_capa_url: string;
}

/** Sala de chat */
export interface SalaChat {
  id: string;
  locacao_id: string;
  participantes: Participante[];
  item: ItemSala;
  ultima_mensagem?: {
    conteudo: string;
    remetente_id: string;
    criado_em: string;
  };
  nao_lidas: number;
  criado_em: string;
  atualizado_em: string;
}

/** Mensagem individual */
export interface Mensagem {
  id: string;
  sala_id: string;
  remetente: Participante;
  conteudo: string;
  lida: boolean;
  criado_em: string;
}

/** Resposta paginada de salas */
export interface SalasResponse {
  results: SalaChat[];
  count: number;
  next: string | null;
  previous: string | null;
}

/** Resposta paginada de mensagens */
export interface MensagensResponse {
  results: Mensagem[];
  count: number;
  next: string | null;
  previous: string | null;
}

// ─── Funções da API ─────────────────────────────────────

/**
 * Lista todas as salas de chat do usuário.
 *
 * GET /chat/salas/
 */
export async function listarSalas(): Promise<SalaChat[]> {
  const response = await apiClient.get<SalasResponse>('chat/salas/');
  return response.data.results;
}

/**
 * Lista as mensagens de uma sala específica.
 *
 * GET /chat/salas/{salaId}/mensagens/
 */
export async function listarMensagens(salaId: string): Promise<Mensagem[]> {
  const response = await apiClient.get<MensagensResponse>(
    `chat/salas/${salaId}/mensagens/`,
  );
  return response.data.results;
}

/**
 * Envia uma mensagem em uma sala.
 *
 * POST /chat/salas/{salaId}/mensagens/
 */
export async function enviarMensagem(
  salaId: string,
  conteudo: string,
): Promise<Mensagem> {
  const response = await apiClient.post<Mensagem>(
    `chat/salas/${salaId}/mensagens/`,
    { conteudo },
  );
  return response.data;
}

/** Re-export por conveniência */
export const chatApi = {
  listarSalas,
  listarMensagens,
  enviarMensagem,
};

export default chatApi;
