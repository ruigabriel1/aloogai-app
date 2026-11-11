/**
 * Paleta de cores da marca Aloogaí
 *
 * Extraída da identidade visual:
 * - Verde escuro: primária, botões, CTAs
 * - Verde médio: sucesso, badges ESG
 * - Amarelo: destaque, impulsionamento
 * - Laranja: secundária, markers no mapa
 * - Laranja escuro: accent, alertas
 */

/** Cores da marca (compartilhadas entre temas) */
export const BrandColors = {
  /** Verde escuro — cor primária, botões e CTAs */
  primary: '#1B7A2B',
  /** Verde escuro com variações */
  primaryLight: '#2E9B3E',
  primaryDark: '#145E21',

  /** Verde médio — sucesso, badges ESG */
  success: '#4CAF50',
  successLight: '#6FCA73',
  successDark: '#388E3C',

  /** Amarelo — destaque, impulsionamento */
  highlight: '#FFC107',
  highlightLight: '#FFD54F',
  highlightDark: '#FFA000',

  /** Laranja — secundária, markers no mapa */
  secondary: '#FF9800',
  secondaryLight: '#FFB74D',
  secondaryDark: '#F57C00',

  /** Laranja escuro — accent, alertas */
  accent: '#E64A19',
  accentLight: '#FF7043',
  accentDark: '#BF360C',

  /** Branco puro e preto puro */
  white: '#FFFFFF',
  black: '#000000',

  /** Transparentes */
  transparent: 'transparent',
  overlay: 'rgba(0, 0, 0, 0.5)',
  overlayLight: 'rgba(0, 0, 0, 0.3)',
} as const;

/** Cores específicas do tema Light */
export const LightThemeColors = {
  ...BrandColors,

  /** Backgrounds */
  background: '#FFFFFF',
  surface: '#F5F5F5',
  surfaceVariant: '#EEEEEE',

  /** Textos */
  text: '#1A1A1A',
  textSecondary: '#666666',
  textTertiary: '#999999',
  textInverse: '#FFFFFF',

  /** Bordas */
  border: '#E0E0E0',
  borderLight: '#F0F0F0',
  borderFocused: '#1B7A2B',

  /** Estados */
  error: '#D32F2F',
  errorLight: '#FFEBEE',
  warning: '#FFA000',
  warningLight: '#FFF8E1',
  info: '#1976D2',
  infoLight: '#E3F2FD',
  successBackground: '#E8F5E9',

  /** Sombras */
  shadow: 'rgba(0, 0, 0, 0.1)',
  shadowMedium: 'rgba(0, 0, 0, 0.15)',
  shadowStrong: 'rgba(0, 0, 0, 0.25)',

  /** Input */
  inputBackground: '#F5F5F5',
  inputBorder: '#E0E0E0',
  inputPlaceholder: '#999999',

  /** Tabs / Navegação */
  tabBarBackground: '#FFFFFF',
  tabBarBorder: '#E0E0E0',
  tabIconDefault: '#999999',
  tabIconActive: '#1B7A2B',

  /** Card */
  cardBackground: '#FFFFFF',
  cardBorder: '#F0F0F0',

  /** Status bar */
  statusBarStyle: 'dark' as const,
} as const;

/** Cores específicas do tema Dark */
export const DarkThemeColors = {
  ...BrandColors,

  /** Backgrounds */
  background: '#121212',
  surface: '#1E1E1E',
  surfaceVariant: '#2C2C2C',

  /** Textos */
  text: '#F5F5F5',
  textSecondary: '#AAAAAA',
  textTertiary: '#777777',
  textInverse: '#1A1A1A',

  /** Bordas */
  border: '#333333',
  borderLight: '#2C2C2C',
  borderFocused: '#4CAF50',

  /** Estados */
  error: '#EF5350',
  errorLight: '#3E1A1A',
  warning: '#FFB74D',
  warningLight: '#3E3318',
  info: '#42A5F5',
  infoLight: '#1A2E3E',
  successBackground: '#1A3E1A',

  /** Sombras */
  shadow: 'rgba(0, 0, 0, 0.3)',
  shadowMedium: 'rgba(0, 0, 0, 0.4)',
  shadowStrong: 'rgba(0, 0, 0, 0.6)',

  /** Input */
  inputBackground: '#2C2C2C',
  inputBorder: '#444444',
  inputPlaceholder: '#777777',

  /** Tabs / Navegação */
  tabBarBackground: '#1E1E1E',
  tabBarBorder: '#333333',
  tabIconDefault: '#777777',
  tabIconActive: '#4CAF50',

  /** Card */
  cardBackground: '#1E1E1E',
  cardBorder: '#333333',

  /** Status bar */
  statusBarStyle: 'light' as const,
} as const;

/** Tipo da paleta de cores por tema (usa string para compatibilidade entre temas) */
export type ThemeColors = {
  [K in keyof typeof LightThemeColors]: string;
};

/** Mapa de cores por tema */
export const Colors = {
  light: LightThemeColors,
  dark: DarkThemeColors,
} as const;

export default Colors;
