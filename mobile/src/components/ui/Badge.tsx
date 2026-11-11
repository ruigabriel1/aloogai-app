/**
 * Componente Badge — Indicador de contagem do Aloogaí
 *
 * Badge pequeno para notificações, contagens de itens não lidos, etc.
 * Adapta automaticamente ao tema Light/Dark.
 */

import React from 'react';
import { View, Text, StyleSheet, type ViewStyle } from 'react-native';
import { useTheme } from '../../theme';
import { FontFamily } from '../../theme/typography';

/** Variantes de cor do badge */
export type BadgeVariant = 'primary' | 'secondary' | 'success' | 'error' | 'warning';

/** Props do componente Badge */
export interface BadgeProps {
  /** Valor exibido (número ou texto curto) */
  value?: number | string;
  /** Variante de cor (padrão: primary) */
  variant?: BadgeVariant;
  /** Exibir apenas como ponto (sem texto) */
  dot?: boolean;
  /** Valor máximo (exibe "99+" se ultrapassar) */
  max?: number;
  /** Visibilidade (padrão: true) */
  visible?: boolean;
  /** Estilos adicionais */
  style?: ViewStyle;
  /** Identificador para testes */
  testID?: string;
}

/** Cores por variante */
function getVariantColor(variant: BadgeVariant): string {
  switch (variant) {
    case 'primary':
      return '#1B7A2B';
    case 'secondary':
      return '#FF9800';
    case 'success':
      return '#4CAF50';
    case 'error':
      return '#D32F2F';
    case 'warning':
      return '#FFA000';
    default:
      return '#1B7A2B';
  }
}

/** Badge de contagem ou indicador pontual */
export function Badge({
  value,
  variant = 'primary',
  dot = false,
  max = 99,
  visible = true,
  style,
  testID,
}: BadgeProps): React.JSX.Element | null {
  if (!visible) return null;

  const backgroundColor = getVariantColor(variant);

  if (dot) {
    return (
      <View
        testID={testID}
        style={[
          styles.dot,
          { backgroundColor },
          style,
        ]}
      />
    );
  }

  const displayValue =
    typeof value === 'number' && value > max ? `${max}+` : String(value ?? '');

  if (!displayValue) return null;

  const isWide = displayValue.length > 1;

  return (
    <View
      testID={testID}
      style={[
        styles.badge,
        { backgroundColor },
        isWide && styles.badgeWide,
        style,
      ]}
    >
      <Text style={styles.text}>{displayValue}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  badge: {
    minWidth: 20,
    height: 20,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  badgeWide: {
    paddingHorizontal: 6,
  },
  text: {
    color: '#FFFFFF',
    fontSize: 11,
    fontFamily: FontFamily.bold,
    textAlign: 'center',
    includeFontPadding: false,
  },
});

export default Badge;
