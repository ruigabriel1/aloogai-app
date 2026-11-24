/**
 * Auth Store — Gerenciamento de autenticação do Aloogaí
 *
 * Estado global com Zustand para tokens JWT, dados do usuário
 * e persistência segura via expo-secure-store.
 */

import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { queryClient } from '../api/queryClient';

/** Usuário logado: espelha o UsuarioPerfilSerializer do backend (GET users/perfil/). */
export interface Usuario {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  tipo_usuario: 'P2P' | 'B2B';
  cpf_cnpj: string;
  telefone: string;
  foto_perfil: string | null;
  kyc_status: string;
  score_esg: number;
  stripe_onboarding_complete: boolean;
  is_locador_ativo: boolean;
  created_at: string;
}

/** Nome para exibir na interface. */
export function nomeDoUsuario(user: Usuario | null): string {
  if (!user) return '';
  const completo = `${user.first_name ?? ''} ${user.last_name ?? ''}`.trim();
  return completo || user.username;
}

/** Interface do store de autenticação */
interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: Usuario | null;
  isAuthenticated: boolean;
  /** Se a verificação inicial de tokens foi concluída */
  isLoading: boolean;

  /** Faz login salvando tokens e usuário */
  login: (token: string, refreshToken: string, user: Usuario) => Promise<void>;
  /** Faz logout limpando tokens, usuário e o cache de dados */
  logout: () => Promise<void>;
  /** Atualiza dados do usuário */
  setUser: (user: Usuario) => void;
  /** Grava os tokens novos após um refresh (o backend rotaciona o refresh) */
  setTokens: (token: string, refreshToken?: string) => Promise<void>;
  /** Carrega tokens salvos ao iniciar o app */
  initialize: () => Promise<void>;
}

const STORAGE_KEYS = {
  ACCESS_TOKEN: 'aloogai_access_token',
  REFRESH_TOKEN: 'aloogai_refresh_token',
  USER_DATA: 'aloogai_user_data',
} as const;

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  refreshToken: null,
  user: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (token, refreshToken, user) => {
    // Sem try/catch: se não der para salvar, o erro sobe para a tela de login.
    await SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN, token);
    await SecureStore.setItemAsync(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
    await SecureStore.setItemAsync(STORAGE_KEYS.USER_DATA, JSON.stringify(user));
    set({ token, refreshToken, user, isAuthenticated: true, isLoading: false });
  },

  logout: async () => {
    try {
      await SecureStore.deleteItemAsync(STORAGE_KEYS.ACCESS_TOKEN);
      await SecureStore.deleteItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
      await SecureStore.deleteItemAsync(STORAGE_KEYS.USER_DATA);
    } catch (error) {
      console.error('Erro ao limpar tokens:', error);
    }
    queryClient.clear();
    set({ token: null, refreshToken: null, user: null, isAuthenticated: false, isLoading: false });
  },

  setUser: (user) => {
    SecureStore.setItemAsync(STORAGE_KEYS.USER_DATA, JSON.stringify(user)).catch((error) =>
      console.error('Erro ao salvar dados do usuário:', error),
    );
    set({ user });
  },

  setTokens: async (token, refreshToken) => {
    await SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN, token);
    if (refreshToken) {
      await SecureStore.setItemAsync(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
    }
    set({ token, refreshToken: refreshToken ?? get().refreshToken });
  },

  initialize: async () => {
    try {
      const token = await SecureStore.getItemAsync(STORAGE_KEYS.ACCESS_TOKEN);
      const refreshToken = await SecureStore.getItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
      const userData = await SecureStore.getItemAsync(STORAGE_KEYS.USER_DATA);

      if (token && refreshToken && userData) {
        const user = JSON.parse(userData) as Usuario;
        set({ token, refreshToken, user, isAuthenticated: true, isLoading: false });
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
