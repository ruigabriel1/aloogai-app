/**
 * API de Autenticação do Aloogaí
 *
 * Login (JWT por e-mail), cadastro e perfil. Os tipos espelham os serializers do backend.
 */

import { apiClient } from './client';
import type { Usuario } from '../store/authStore';

/** Payload de login */
export interface LoginPayload {
  email: string;
  password: string;
}

/** Resposta de POST auth/token/ e auth/token/refresh/ */
export interface TokenResponse {
  access: string;
  refresh: string;
}

/** Sessão completa: tokens + perfil do usuário */
export interface Sessao extends TokenResponse {
  user: Usuario;
}

/** Payload de POST users/registro/ (UsuarioRegistroSerializer) */
export interface RegisterPayload {
  email: string;
  first_name: string;
  last_name?: string;
  cpf_cnpj: string;
  telefone: string;
  password: string;
  password_confirm: string;
  tipo_usuario: 'P2P' | 'B2B';
}

/** Busca o perfil com um token específico (antes de ele estar salvo no store). */
async function buscarPerfilComToken(access: string): Promise<Usuario> {
  const response = await apiClient.get<Usuario>('users/perfil/', {
    headers: { Authorization: `Bearer ${access}` },
  });
  return response.data;
}

/**
 * Faz login com e-mail e senha e já traz o perfil.
 *
 * POST auth/token/ devolve só os tokens; o perfil vem de GET users/perfil/.
 */
export async function login(payload: LoginPayload): Promise<Sessao> {
  const response = await apiClient.post<TokenResponse>('auth/token/', {
    username: payload.email.trim().toLowerCase(), // o backend aceita e-mail no campo username
    password: payload.password,
  });
  const user = await buscarPerfilComToken(response.data.access);
  return { ...response.data, user };
}

/**
 * Cadastra o usuário e já faz login.
 *
 * POST users/registro/ não devolve tokens, então o login vem em seguida.
 */
export async function register(payload: RegisterPayload): Promise<Sessao> {
  await apiClient.post('users/registro/', payload);
  return login({ email: payload.email, password: payload.password });
}

/** GET users/perfil/ com o token atual. */
export async function buscarPerfil(): Promise<Usuario> {
  const response = await apiClient.get<Usuario>('users/perfil/');
  return response.data;
}

/**
 * Converte o erro de validação do Django REST Framework numa mensagem legível.
 * Ex.: { email: ["Já existe uma conta com este e-mail."] } → "Já existe uma conta com este e-mail."
 */
export function mensagemDeErro(error: unknown, padrao: string): string {
  const data = (error as { response?: { data?: unknown } })?.response?.data;
  if (!data || typeof data !== 'object') return padrao;
  const registro = data as Record<string, unknown>;
  if (typeof registro.detail === 'string') return registro.detail;
  for (const valor of Object.values(registro)) {
    if (Array.isArray(valor) && typeof valor[0] === 'string') return valor[0];
    if (typeof valor === 'string') return valor;
  }
  return padrao;
}

export const authApi = { login, register, buscarPerfil };

export default authApi;
