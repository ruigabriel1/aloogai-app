/**
 * Auth Store — Gerenciamento de autenticação do Aloogaí
 *
 * Estado global com Zustand para tokens JWT, dados do usuário
 * e persistência segura via expo-secure-store.
 */

import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

/** Dados do usuário autenticado */
export interface Usuario {
  id: string;
  nome: string;
  email: string;
  tipo_conta: 'P2P' | 'B2B';
  cpf?: string;
  telefone?: string;
  foto_perfil?: string;
  score_esg?: number;
  avaliacao_media?: number;
}

/** Interface do store de autenticação */
interface AuthState {
  /** Token JWT de acesso */
  token: string | null;
  /** Token JWT de refresh */
  refreshToken: string | null;
  /** Dados do usuário logado */
  user: Usuario | null;
  /** Se o usuário está autenticado */
  isAuthenticated: boolean;
  /** Se a verificação inicial de tokens foi concluída */
  isLoading: boolean;

  /** Faz login salvando tokens e usuário */
  login: (token: string, refreshToken: string, user: Usuario) => Promise<void>;
  /** Faz logout limpando tudo */
  logout: () => Promise<void>;
  /** Atualiza dados do usuário */
  setUser: (user: Usuario) => void;
  /** Atualiza apenas o token de acesso (após refresh) */
  setToken: (token: string) => Promise<void>;
  /** Carrega tokens salvos ao iniciar o app */
  initialize: () => Promise<void>;
}

/** Chaves para armazenamento seguro */
const STORAGE_KEYS = {
  ACCESS_TOKEN: 'aloogai_access_token',
  REFRESH_TOKEN: 'aloogai_refresh_token',
  USER_DATA: 'aloogai_user_data',
} as const;

/**
 * Store de autenticação com Zustand.
 *
 * Persiste tokens em SecureStore para segurança.
 * Ao iniciar o app, chama initialize() para restaurar a sessão.
 */
export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  refreshToken: null,
  user: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (token: string, refreshToken: string, user: Usuario) => {
    try {
      await SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN, token);
      await SecureStore.setItemAsync(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
      await SecureStore.setItemAsync(STORAGE_KEYS.USER_DATA, JSON.stringify(user));
    } catch (error) {
      console.error('Erro ao salvar tokens:', error);
    }

    set({
      token,
      refreshToken,
      user,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  logout: async () => {
    try {
      await SecureStore.deleteItemAsync(STORAGE_KEYS.ACCESS_TOKEN);
      await SecureStore.deleteItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
      await SecureStore.deleteItemAsync(STORAGE_KEYS.USER_DATA);
    } catch (error) {
      console.error('Erro ao limpar tokens:', error);
    }

    set({
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  setUser: (user: Usuario) => {
    SecureStore.setItemAsync(STORAGE_KEYS.USER_DATA, JSON.stringify(user)).catch(
      (error) => console.error('Erro ao salvar dados do usuário:', error),
    );
    set({ user });
  },

  setToken: async (token: string) => {
    try {
      await SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN, token);
    } catch (error) {
      console.error('Erro ao atualizar token:', error);
    }
    set({ token });
  },

  initialize: async () => {
    try {
      const token = await SecureStore.getItemAsync(STORAGE_KEYS.ACCESS_TOKEN);
      const refreshToken = await SecureStore.getItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
      const userData = await SecureStore.getItemAsync(STORAGE_KEYS.USER_DATA);

      if (token && refreshToken && userData) {
        const user = JSON.parse(userData) as Usuario;
        set({
          token,
          refreshToken,
          user,
          isAuthenticated: true,
          isLoading: false,
        });
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
      console.error('Erro ao restaurar sessão:', error);
      set({ isLoading: false });
    }
  },
}));

export default useAuthStore;
