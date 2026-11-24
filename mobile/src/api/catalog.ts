/**
 * API do Catálogo do Aloogaí
 *
 * Busca por proximidade, categorias, detalhe, criação de item e upload de foto.
 * Os tipos espelham backend/apps/catalog/serializers.py.
 */

import { apiClient } from './client';

// ─── Tipos ──────────────────────────────────────────────

export type Camada = 'ESSENTIAL' | 'PRO' | 'B2B';

/** UsuarioResumoSerializer */
export interface LocadorResumo {
  id: string;
  nome: string;
  first_name: string;
  foto_perfil: string | null;
  score_esg: number;
  tipo_usuario: 'P2P' | 'B2B';
}

/** ItemListSerializer (feed e mapa) */
export interface ItemResumo {
  id: string;
  titulo: string;
  descricao: string;
  camada: Camada;
  status: 'RASCUNHO' | 'ATIVO' | 'PAUSADO' | 'INATIVO';
  aprovado_para_uso: boolean;
  categoria: string;
  categoria_nome: string;
  categoria_icone: string;
  preco_diaria: string;
  valor_caucao: string;
  is_destacado: boolean;
  avaliacao_media: number;
  total_avaliacoes: number;
  foto_capa_url: string | null;
  distancia_km: number | null;
  latitude: number | null;
  longitude: number | null;
  locador: LocadorResumo;
}

/** Item com coordenadas garantidas (para o mapa) */
export type ItemNoMapa = ItemResumo & { latitude: number; longitude: number };

/** Resposta paginada do DRF */
export interface Paginado<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface FiltrosBusca {
  camada?: Camada | null;
  categoria?: string | null;
  preco_max?: number | null;
  ordenar_por?: 'distancia' | 'preco' | 'avaliacao';
  busca?: string;
  page?: number;
}

/** CategoriaSerializer */
export interface Categoria {
  id: string;
  nome: string;
  slug: string;
  descricao: string;
  icone: string;
  ordem: number;
}

/** FotoItemSerializer */
export interface FotoItem {
  id: string;
  item: string;
  imagem: string;
  is_capa: boolean;
  ordem: number;
  created_at: string;
}

/** ItemDetailSerializer */
export interface ItemDetalhe {
  id: string;
  titulo: string;
  descricao: string;
  camada: Camada;
  status: 'RASCUNHO' | 'ATIVO' | 'PAUSADO' | 'INATIVO';
  preco_diaria: string;
  valor_caucao: string;
  latitude: number | null;
  longitude: number | null;
  foto_capa_url: string | null;
  endereco_texto: string;
  requer_licenca: boolean;
  aprovado_para_uso: boolean;
  is_destacado: boolean;
  avaliacao_media: number;
  total_avaliacoes: number;
  total_locacoes: number;
  categoria: string;
  categoria_nome: string;
  locador: LocadorResumo;
  fotos: FotoItem[];
  visivel_no_mapa: boolean;
  created_at: string;
  updated_at: string;
}

/** Payload de POST catalog/itens/ (ItemCreateUpdateSerializer) */
export interface NovoItemPayload {
  titulo: string;
  descricao: string;
  categoria: string;
  preco_diaria: string;
  valor_caucao: string;
  latitude: number;
  longitude: number;
  camada?: Camada;
  endereco_texto?: string;
}

// ─── Funções da API ─────────────────────────────────────

/** GET catalog/itens/proximos/?lat&lng&raio_km */
export async function buscarItensProximidade(
  lat: number,
  lng: number,
  raio_km: number = 5,
  filtros?: FiltrosBusca,
): Promise<Paginado<ItemResumo>> {
  const params: Record<string, string | number> = { lat, lng, raio_km };
  if (filtros?.camada) params.camada = filtros.camada;
  if (filtros?.categoria) params.categoria = filtros.categoria;
  if (filtros?.preco_max) params.preco_max = filtros.preco_max;
  if (filtros?.ordenar_por) params.ordenar_por = filtros.ordenar_por;
  if (filtros?.busca) params.busca = filtros.busca;
  if (filtros?.page) params.page = filtros.page;

  const response = await apiClient.get<Paginado<ItemResumo>>('catalog/itens/proximos/', { params });
  return response.data;
}

/** GET catalog/categorias/ (lista simples, sem paginação) */
export async function buscarCategorias(): Promise<Categoria[]> {
  const response = await apiClient.get<Categoria[]>('catalog/categorias/');
  return response.data;
}

/** GET catalog/itens/{id}/ */
export async function buscarItemDetalhe(id: string): Promise<ItemDetalhe> {
  const response = await apiClient.get<ItemDetalhe>(`catalog/itens/${id}/`);
  return response.data;
}

/** POST catalog/itens/ (o item nasce ATIVO) */
export async function criarItem(dados: NovoItemPayload): Promise<{ id: string }> {
  const response = await apiClient.post<{ id: string }>('catalog/itens/', dados);
  return response.data;
}

/**
 * POST catalog/fotos/ (multipart). `uri` é o arquivo local escolhido no ImagePicker.
 */
export async function enviarFotoItem(itemId: string, uri: string, isCapa = true): Promise<FotoItem> {
  const nome = uri.split('/').pop() || 'foto.jpg';
  const extensao = nome.split('.').pop()?.toLowerCase();
  const tipo = extensao === 'png' ? 'image/png' : 'image/jpeg';

  const form = new FormData();
  form.append('item', itemId);
  form.append('is_capa', isCapa ? 'true' : 'false');
  // React Native aceita { uri, name, type } como arquivo no FormData
  form.append('imagem', { uri, name: nome, type: tipo } as unknown as Blob);

  const response = await apiClient.post<FotoItem>('catalog/fotos/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

/** GET catalog/itens/?meus=true — itens do usuário em qualquer status */
export async function buscarMeusItens(): Promise<ItemResumo[]> {
  const response = await apiClient.get<Paginado<ItemResumo>>('catalog/itens/', {
    params: { meus: 'true' },
  });
  return response.data.results;
}

export const catalogApi = {
  buscarItensProximidade,
  buscarCategorias,
  buscarItemDetalhe,
  criarItem,
  enviarFotoItem,
  buscarMeusItens,
};

export default catalogApi;
