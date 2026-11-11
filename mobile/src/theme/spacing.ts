/**
 * Sistema de espaçamento do Aloogaí
 *
 * Baseado em grid de 4px para consistência visual.
 * Use sempre estes valores ao invés de números mágicos.
 */

/** Grid de espaçamento base (múltiplos de 4px) */
export const Spacing = {
  /** 0px — sem espaçamento */
  none: 0,
  /** 2px — micro espaçamento */
  xxs: 2,
  /** 4px — espaçamento extra pequeno */
  xs: 4,
  /** 8px — espaçamento pequeno */
  sm: 8,
  /** 12px — espaçamento pequeno-médio */
  ms: 12,
  /** 16px — espaçamento médio (padrão) */
  md: 16,
  /** 20px — espaçamento médio-grande */
  ml: 20,
  /** 24px — espaçamento grande */
  lg: 24,
  /** 32px — espaçamento extra grande */
  xl: 32,
  /** 40px — espaçamento 2x grande */
  xxl: 40,
  /** 48px — espaçamento 3x grande */
  xxxl: 48,
  /** 64px — espaçamento 4x grande */
  huge: 64,
  /** 80px — espaçamento hero */
  hero: 80,
} as const;

/** Raios de borda padrão */
export const BorderRadius = {
  /** 0px — sem arredondamento */
  none: 0,
  /** 4px — arredondamento sutil */
  xs: 4,
  /** 8px — arredondamento pequeno */
  sm: 8,
  /** 12px — arredondamento médio */
  md: 12,
  /** 16px — arredondamento grande */
  lg: 16,
  /** 20px — arredondamento extra grande */
  xl: 20,
  /** 24px — arredondamento 2x grande */
  xxl: 24,
  /** 999px — totalmente arredondado (pill) */
  full: 999,
} as const;

/** Tamanhos de ícone padrão */
export const IconSize = {
  /** 16px */
  xs: 16,
  /** 20px */
  sm: 20,
  /** 24px — padrão */
  md: 24,
  /** 28px */
  lg: 28,
  /** 32px */
  xl: 32,
  /** 48px */
  xxl: 48,
} as const;

/** Alturas de hit area mínimas para acessibilidade */
export const HitSlop = {
  /** Padrão — 44x44 conforme guidelines de acessibilidade */
  default: { top: 10, bottom: 10, left: 10, right: 10 },
  /** Grande — para botões menores */
  large: { top: 16, bottom: 16, left: 16, right: 16 },
} as const;

/** Sombras padrão (para plataformas) */
export const Shadows = {
  /** Sombra leve — cards */
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 2,
    elevation: 2,
  },
  /** Sombra média — cards em hover/destaque */
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 4,
    elevation: 4,
  },
  /** Sombra forte — modais, bottom sheets */
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.16,
    shadowRadius: 8,
    elevation: 8,
  },
  /** Sombra extra forte — overlays */
  xl: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.2,
    shadowRadius: 16,
    elevation: 12,
  },
} as const;

export default Spacing;
