/**
 * API de Chat do Aloogaí
 *
 * Os tipos espelham backend/apps/chat/serializers.py.
 */

import { apiClient } from './client';
import type { Paginado } from './catalog';

// ─── Tipos ──────────────────────────────────────────────

/** SalaChatSerializer */
export interface SalaChat {
  id: string;
  locacao: string;
  locador: string;
  locatario: string;
  item_titulo: string;
  outro_participante: { id: string; nome: string };
  ativa: boolean;
  chat_permitido: boolean;
  total_mensagens: number;
  nao_lidas: number;
  ultima_mensagem: {
    id: string;
    remetente: string;
    conteudo: string;
    tipo: string;
    created_at: string;
  } | null;
  created_at: string;
}

/** MensagemSerializer (REST) e evento "mensagem" do WebSocket */
export interface Mensagem {
  id: string;
  sala: string;
  remetente: string;
  conteudo: string;
  tipo: string;
  lida_em: string | null;
  created_at: string;
}

// ─── Funções da API ─────────────────────────────────────

/** GET chat/salas/ */
export async function listarSalas(): Promise<SalaChat[]> {
  const response = await apiClient.get<Paginado<SalaChat>>('chat/salas/');
  return response.data.results;
}

/** GET chat/salas/{id}/ */
export async function obterSala(salaId: string): Promise<SalaChat> {
  const response = await apiClient.get<SalaChat>(`chat/salas/${salaId}/`);
  return response.data;
}

/** GET chat/salas/{id}/mensagens/ */
export async function listarMensagens(salaId: string): Promise<Mensagem[]> {
  const response = await apiClient.get<Paginado<Mensagem> | Mensagem[]>(
    `chat/salas/${salaId}/mensagens/`,
  );
  return Array.isArray(response.data) ? response.data : response.data.results;
}

/** POST chat/salas/{id}/mensagens/ (alternativa ao WebSocket) */
export async function enviarMensagem(salaId: string, conteudo: string): Promise<Mensagem> {
  const response = await apiClient.post<Mensagem>(`chat/salas/${salaId}/mensagens/`, {
    conteudo,
  });
  return response.data;
}

/** POST chat/salas/{id}/mensagens/marcar-lidas/ */
export async function marcarLidas(salaId: string): Promise<void> {
  await apiClient.post(`chat/salas/${salaId}/mensagens/marcar-lidas/`);
}

export const chatApi = { listarSalas, obterSala, listarMensagens, enviarMensagem, marcarLidas };

export default chatApi;
