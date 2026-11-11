/**
 * Hook de controle de tema (Light/Dark) do Aloogaí
 *
 * Usa Zustand para estado global do tema e respeita
 * a preferência do sistema (useColorScheme) como padrão.
 */

import { useColorScheme } from 'react-native';
import { create } from 'zustand';

/** Modos de tema suportados */
export type ThemeMode = 'light' | 'dark' | 'system';

/** Interface do store de tema */
interface ThemeModeStore {
  /** Modo selecionado pelo usuário (ou 'system' para automático) */
  mode: ThemeMode;
  /** Define o modo de tema */
  setMode: (mode: ThemeMode) => void;
  /** Alterna entre light e dark (ignora system) */
  toggle: () => void;
}

/**
 * Store Zustand para gerenciar o modo de tema.
 * Armazena a preferência do usuário (light, dark ou system).
 */
export const useThemeModeStore = create<ThemeModeStore>((set, get) => ({
  mode: 'system',
  setMode: (mode: ThemeMode) => set({ mode }),
  toggle: () => {
    const current = get().mode;
    if (current === 'light') {
      set({ mode: 'dark' });
    } else {
      set({ mode: 'light' });
    }
  },
}));

/**
 * Hook que retorna o modo de tema efetivo (light ou dark).
 *
 * Se o modo for 'system', usa a preferência do dispositivo.
 * Caso contrário, retorna o modo selecionado pelo usuário.
 */
export function useThemeMode(): 'light' | 'dark' {
  const { mode } = useThemeModeStore();
  const systemScheme = useColorScheme();

  if (mode === 'system') {
    return systemScheme === 'dark' ? 'dark' : 'light';
  }

  return mode;
}

export default useThemeMode;
