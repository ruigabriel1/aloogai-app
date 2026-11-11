/**
 * Componente Card — Container com elevação do Aloogaí
 *
 * Container com sombra/elevação, borda arredondada.
 * Adapta automaticamente ao tema Light/Dark.
 */

import React from 'react';
import {
  View,
  TouchableOpacity,
  StyleSheet,
  type ViewStyle,
} from 'react-native';
import { useTheme } from '../../theme';
import { BorderRadius, Spacing, Shadows } from '../../theme/spacing';

/** Variantes de elevação do card */
export type CardElevation = 'none' | 'sm' | 'md' | 'lg';

/** Props do componente Card */
export interface CardProps {
  /** Conteúdo do card */
  children: React.ReactNode;
  /** Nível de elevação/sombra (padrão: sm) */
  elevation?: CardElevation;
  /** Callback ao pressionar (torna o card clicável) */
  onPress?: () => void;
  /** Padding interno (padrão: md) */
  padding?: keyof typeof Spacing;
  /** Borda arredondada (padrão: md) */
  borderRadius?: keyof typeof BorderRadius;
  /** Estilos adicionais */
  style?: ViewStyle;
  /** Identificador para testes */
  testID?: string;
}

/** Card container reutilizável com sombra adaptável ao tema */
export function Card({
  children,
  elevation = 'sm',
  onPress,
  padding = 'md',
  borderRadius = 'md',
  style,
  testID,
}: CardProps): React.JSX.Element {
  const { colors } = useTheme();

  const shadowStyle = elevation !== 'none' ? Shadows[elevation] : {};

  const containerStyle: ViewStyle = {
    backgroundColor: colors.cardBackground,
    borderRadius: BorderRadius[borderRadius],
    borderWidth: 1,
    borderColor: colors.cardBorder,
    padding: Spacing[padding],
    ...shadowStyle,
  };

  if (onPress) {
    return (
      <TouchableOpacity
        testID={testID}
        onPress={onPress}
        activeOpacity={0.7}
        style={[styles.container, containerStyle, style]}
      >
        {children}
      </TouchableOpacity>
    );
  }

  return (
    <View testID={testID} style={[styles.container, containerStyle, style]}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    overflow: 'hidden',
  },
});

export default Card;
