/**
 * API Client — Instância Axios configurada do Aloogaí
 *
 * - baseURL para o backend Django
 * - Interceptor de request: injeta Bearer token
 * - Interceptor de response 401: tenta refresh automático
 */

import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../store/authStore';

/** URL base da API (IP da máquina local para testes em celular físico) */
const API_BASE_URL = 'http://192.168.25.18:8000/api/v1/';

/** Timeout padrão de 30 segundos */
const TIMEOUT = 30000;

/**
 * Instância Axios configurada para o backend do Aloogaí.
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

/** Flag para evitar loop infinito de refresh */
let isRefreshing = false;

/** Fila de requests aguardando o refresh do token */
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

/**
 * Processa a fila de requests pendentes após refresh.
 */
function processQueue(error: unknown, token: string | null = null): void {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
}

/**
 * Interceptor de request: injeta o Bearer token do authStore.
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const { token } = useAuthStore.getState();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

/**
 * Interceptor de response: trata 401 com refresh automático.
 *
 * Se receber 401:
 * 1. Tenta fazer refresh do token
 * 2. Se sucesso, re-envia o request original
 * 3. Se falhar, faz logout do usuário
 */
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Se não for 401 ou já tentou retry, rejeita
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    // Se já está fazendo refresh, adiciona na fila
    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return apiClient(originalRequest);
        })
        .catch((err) => Promise.reject(err));
    }

    originalRequest._retry = true;
    isRefreshing = true;

    const { refreshToken, setToken, logout } = useAuthStore.getState();

    if (!refreshToken) {
      isRefreshing = false;
      await logout();
      return Promise.reject(error);
    }

    try {
      const response = await axios.post(`${API_BASE_URL}auth/token/refresh/`, {
        refresh: refreshToken,
      });

      const newToken = response.data.access as string;
      await setToken(newToken);

      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
      }

      processQueue(null, newToken);
      isRefreshing = false;

      return apiClient(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      isRefreshing = false;
      await logout();
      return Promise.reject(refreshError);
    }
  },
);

export default apiClient;
