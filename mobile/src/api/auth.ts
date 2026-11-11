/**
 * API de Autenticação do Aloogaí
 *
 * Funções para login, registro e refresh de token JWT.
 * Usa o apiClient configurado com interceptors.
 */

import { apiClient } from './client';
import type { Usuario } from '../store/authStore';

/** Payload de login */
export interface LoginPayload {
  email: string;
  password: string;
}

/** Resposta de login / refresh */
export interface TokenResponse {
  access: string;
  refresh: string;
}

/** Resposta de login completa (com dados do usuário) */
export interface LoginResponse extends TokenResponse {
  user: Usuario;
}

/** Payload de registro */
export interface RegisterPayload {
  nome: string;
  email: string;
  cpf: string;
  telefone: string;
  password: string;
  password_confirm: string;
  tipo_conta: 'P2P' | 'B2B';
}

/** Resposta de registro */
export interface RegisterResponse {
  user: Usuario;
  access: string;
  refresh: string;
}

/**
 * Faz login com email e senha.
 *
 * POST /auth/token/
 */
export async function login(payload: LoginPayload): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>('auth/token/', {
    username: payload.email, // O backend espera o campo 'username'
    password: payload.password
  });
  return response.data;
}

/**
 * Registra um novo usuário.
 *
 * POST /users/registro/
 */
export async function register(payload: RegisterPayload): Promise<RegisterResponse> {
  const response = await apiClient.post<RegisterResponse>('users/registro/', payload);
  return response.data;
}

/**
 * Renova o token de acesso usando o refresh token.
 *
 * POST /auth/token/refresh/
 */
export async function refreshToken(refresh: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('auth/token/refresh/', {
    refresh,
  });
  return response.data;
}

/** Re-export por conveniência */
export const authApi = {
  login,
  register,
  refreshToken,
};

export default authApi;
