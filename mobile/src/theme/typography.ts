/**
 * Tipografia do Aloogaí
 *
 * Usa a fonte Inter carregada via expo-font.
 * Define tamanhos, pesos e estilos de texto padronizados.
 */

/** Famílias de fonte disponíveis */
export const FontFamily = {
  regular: 'Inter-Regular',
  medium: 'Inter-Medium',
  semiBold: 'Inter-SemiBold',
  bold: 'Inter-Bold',
  /** Fallback para quando a fonte ainda não carregou */
  fallback: 'System',
} as const;

/** Tamanhos de fonte padronizados */
export const FontSize = {
  /** 10px — captions muito pequenos */
  xs: 10,
  /** 12px — captions, labels menores */
  sm: 12,
  /** 14px — textos secundários, labels */
  md: 14,
  /** 16px — corpo de texto padrão */
  base: 16,
  /** 18px — subtítulos */
  lg: 18,
  /** 20px — títulos de seção */
  xl: 20,
  /** 24px — títulos de tela */
  xxl: 24,
  /** 28px — headings grandes */
  xxxl: 28,
  /** 32px — display */
  display: 32,
  /** 40px — hero text */
  hero: 40,
} as const;

/** Alturas de linha relativas ao tamanho da fonte */
export const LineHeight = {
  tight: 1.2,
  normal: 1.4,
  relaxed: 1.6,
  loose: 1.8,
} as const;

/** Pesos de fonte numéricos */
export const FontWeight = {
  regular: '400' as const,
  medium: '500' as const,
  semiBold: '600' as const,
  bold: '700' as const,
} as const;

/** Estilos de texto pré-definidos */
export const TextStyles = {
  /** Hero — texto principal de destaque */
  hero: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.hero,
    lineHeight: FontSize.hero * LineHeight.tight,
  },
  /** Display — títulos de seção grandes */
  display: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.display,
    lineHeight: FontSize.display * LineHeight.tight,
  },
  /** H1 — título principal da tela */
  h1: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.xxxl,
    lineHeight: FontSize.xxxl * LineHeight.tight,
  },
  /** H2 — subtítulo da tela */
  h2: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.xxl,
    lineHeight: FontSize.xxl * LineHeight.tight,
  },
  /** H3 — título de seção */
  h3: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.xl,
    lineHeight: FontSize.xl * LineHeight.normal,
  },
  /** H4 — subtítulo de seção */
  h4: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.lg,
    lineHeight: FontSize.lg * LineHeight.normal,
  },
  /** Body — texto padrão */
  body: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.base,
    lineHeight: FontSize.base * LineHeight.relaxed,
  },
  /** Body Medium — texto padrão com ênfase */
  bodyMedium: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.base,
    lineHeight: FontSize.base * LineHeight.relaxed,
  },
  /** Body Bold — texto padrão negrito */
  bodyBold: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.base,
    lineHeight: FontSize.base * LineHeight.relaxed,
  },
  /** Body Small — texto secundário */
  bodySmall: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.md,
    lineHeight: FontSize.md * LineHeight.relaxed,
  },
  /** Label — rótulos de inputs e categorias */
  label: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.md,
    lineHeight: FontSize.md * LineHeight.normal,
  },
  /** Label Small — rótulos menores */
  labelSmall: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.sm,
    lineHeight: FontSize.sm * LineHeight.normal,
  },
  /** Caption — textos auxiliares pequenos */
  caption: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.sm,
    lineHeight: FontSize.sm * LineHeight.normal,
  },
  /** Overline — rótulos superiores minúsculos */
  overline: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.xs,
    lineHeight: FontSize.xs * LineHeight.normal,
    letterSpacing: 1.5,
    textTransform: 'uppercase' as const,
  },
  /** Button — texto de botão */
  button: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.base,
    lineHeight: FontSize.base * LineHeight.tight,
    letterSpacing: 0.5,
  },
  /** Button Small — texto de botão pequeno */
  buttonSmall: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.md,
    lineHeight: FontSize.md * LineHeight.tight,
    letterSpacing: 0.5,
  },
} as const;

export const Typography = {
  FontFamily,
  FontSize,
  LineHeight,
  FontWeight,
  TextStyles,
} as const;

export default Typography;
