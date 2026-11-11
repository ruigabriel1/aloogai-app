/**
 * Módulo central do Design System do Aloogaí
 *
 * Re-exporta todos os tokens de design e fornece
 * o hook useTheme() para acesso ao tema ativo.
 */

import { Colors, type ThemeColors, LightThemeColors, DarkThemeColors, BrandColors } from './colors';
import { Typography, FontFamily, FontSize, LineHeight, FontWeight, TextStyles } from './typography';
import { Spacing, BorderRadius, IconSize, HitSlop, Shadows } from './spacing';
import { useThemeMode, useThemeModeStore, type ThemeMode } from '../hooks/useThemeMode';

/**
 * Hook principal do tema.
 *
 * Retorna as cores do tema ativo (light ou dark),
 * juntamente com o modo atual e a função de toggle.
 *
 * @example
 * ```tsx
 * const { colors, isDark } = useTheme();
 * <View style={{ backgroundColor: colors.background }}>
 *   <Text style={{ color: colors.text }}>Olá!</Text>
 * </View>
 * ```
 */
export function useTheme() {
  const themeMode = useThemeMode();
  const isDark = themeMode === 'dark';
  const colors: ThemeColors = isDark ? DarkThemeColors : LightThemeColors;
  const { toggle, setMode, mode } = useThemeModeStore();

  return {
    /** Cores do tema ativo */
    colors,
    /** Se o tema escuro está ativo */
    isDark,
    /** Modo atual: 'light', 'dark' ou 'system' */
    mode,
    /** Alterna entre light e dark */
    toggle,
    /** Define o modo de tema */
    setMode,
    /** Tokens de tipografia */
    typography: Typography,
    /** Tokens de espaçamento */
    spacing: Spacing,
    /** Tokens de borda */
    borderRadius: BorderRadius,
    /** Tamanhos de ícone */
    iconSize: IconSize,
    /** Sombras padrão */
    shadows: Shadows,
  };
}

/** Tipo do retorno de useTheme */
export type Theme = ReturnType<typeof useTheme>;

// Re-exports
export {
  Colors,
  BrandColors,
  LightThemeColors,
  DarkThemeColors,
  Typography,
  FontFamily,
  FontSize,
  LineHeight,
  FontWeight,
  TextStyles,
  Spacing,
  BorderRadius,
  IconSize,
  HitSlop,
  Shadows,
  useThemeMode,
  useThemeModeStore,
};

export type { ThemeColors, ThemeMode };
