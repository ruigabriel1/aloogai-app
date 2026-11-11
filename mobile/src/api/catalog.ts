/**
 * API de Catálogo do Aloogaí
 *
 * Funções para busca de itens por proximidade, categorias
 * e detalhes de itens individuais.
 * Endpoints: /catalog/
 */

import { apiClient } from './client';

// ─── Tipos ──────────────────────────────────────────────

/** Dados do locador resumido */
export interface LocadorResumo {
  id: string;
  nome: string;
  score_esg: number;
  avaliacao_media: number;
  foto_perfil?: string;
}

/** Item retornado na busca por proximidade */
export interface ItemProximidade {
  id: string;
  titulo: string;
  descricao: string;
  camada: 'ESSENTIAL' | 'PRO' | 'B2B';
  preco_diaria: string;
  valor_caucao: string;
  distancia_km: number;
  is_destacado: boolean;
  avaliacao_media: number;
  foto_capa_url: string;
  locador: LocadorResumo;
  categoria: CategoriaResumo;
  latitude: number;
  longitude: number;
}

/** Resposta GeoJSON de busca por proximidade */
export interface BuscaProximidadeResponse {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    geometry: {
      type: 'Point';
      coordinates: [number, number]; // [lng, lat]
    };
    properties: ItemProximidade;
  }>;
  count: number;
  page: number;
  page_size: number;
}

/** Filtros da busca por proximidade */
export interface FiltrosBusca {
  camada?: 'ESSENTIAL' | 'PRO' | 'B2B' | null;
  categoria_id?: string | null;
  preco_max?: number | null;
  ordenar_por?: 'distancia' | 'preco' | 'avaliacao';
  page?: number;
  page_size?: number;
  q?: string;
}

/** Categoria resumida */
export interface CategoriaResumo {
  id: string;
  nome: string;
  icone: string;
  slug: string;
}

/** Resposta da lista de categorias */
export interface CategoriasResponse {
  results: CategoriaResumo[];
  count: number;
}

/** Foto do item */
export interface FotoItem {
  id: string;
  url: string;
  ordem: number;
  is_capa: boolean;
}

/** Item detalhado */
export interface ItemDetalhe {
  id: string;
  titulo: string;
  descricao: string;
  camada: 'ESSENTIAL' | 'PRO' | 'B2B';
  preco_diaria: string;
  valor_caucao: string;
  avaliacao_media: number;
  total_avaliacoes: number;
  total_locacoes: number;
  is_destacado: boolean;
  requer_licenca: boolean;
  aprovado_para_uso: boolean;
  locador: LocadorResumo;
  categoria: CategoriaResumo;
  fotos: FotoItem[];
  latitude: number;
  longitude: number;
  criado_em: string;
  atualizado_em: string;
}

// ─── Funções da API ─────────────────────────────────────

/**
 * Busca itens por proximidade geográfica.
 *
 * GET /catalog/itens/proximos/?lat=X&lng=Y&raio_km=Z
 */
export async function buscarItensProximidade(
  lat: number,
  lng: number,
  raio_km: number = 5,
  filtros?: FiltrosBusca,
): Promise<BuscaProximidadeResponse> {
  const params: Record<string, string | number> = {
    lat,
    lng,
    raio_km,
  };

  if (filtros?.camada) params.camada = filtros.camada;
  if (filtros?.categoria_id) params.categoria_id = filtros.categoria_id;
  if (filtros?.preco_max) params.preco_max = filtros.preco_max;
  if (filtros?.ordenar_por) params.ordenar_por = filtros.ordenar_por;
  if (filtros?.page) params.page = filtros.page;
  if (filtros?.page_size) params.page_size = filtros.page_size;
  if (filtros?.q) params.q = filtros.q;

  const response = await apiClient.get<BuscaProximidadeResponse>(
    'catalog/itens/proximos/',
    { params },
  );
  return response.data;
}

/**
 * Busca todas as categorias disponíveis.
 *
 * GET /catalog/categorias/
 */
export async function buscarCategorias(): Promise<CategoriaResumo[]> {
  const response = await apiClient.get<CategoriasResponse>('catalog/categorias/');
  return response.data.results;
}

/**
 * Busca detalhes de um item específico.
 *
 * GET /catalog/itens/{id}/
 */
export async function buscarItemDetalhe(id: string): Promise<ItemDetalhe> {
  const response = await apiClient.get<ItemDetalhe>(`catalog/itens/${id}/`);
  return response.data;
}

/**
 * Cria um novo item no catálogo do usuário.
 * 
 * POST /catalog/itens/
 */
export async function criarItem(dados: Partial<ItemDetalhe>): Promise<ItemDetalhe> {
  const response = await apiClient.post<ItemDetalhe>('catalog/itens/', dados);
  return response.data;
}

/**
 * Busca itens do próprio usuário logado.
 * 
 * GET /catalog/itens/meus/
 */
export async function buscarMeusItens(): Promise<ItemDetalhe[]> {
  const response = await apiClient.get<ItemDetalhe[]>('catalog/itens/', { params: { is_owner: true } });
  // O backend deve retornar uma listagem paginada ou direta
  // Vamos tratar caso venha um array direto ou { results: [] }
  const data = response.data as any;
  if (data && Array.isArray(data.results)) {
    return data.results;
  }
  return Array.isArray(data) ? data : [];
}

/** Re-export por conveniência */
export const catalogApi = {
  buscarItensProximidade,
  buscarCategorias,
  buscarItemDetalhe,
  criarItem,
  buscarMeusItens,
};

export default catalogApi;
