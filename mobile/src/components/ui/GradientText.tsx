/**
 * Componente GradientText — Texto com gradiente da marca Aloogaí
 *
 * Simula um gradiente verde→laranja usando MaskedView (se disponível)
 * ou fallback para cor sólida da marca.
 */

import React from 'react';
import { Text, StyleSheet, type TextStyle } from 'react-native';
import { BrandColors } from '../../theme/colors';
import { TextStyles, FontFamily } from '../../theme/typography';

/** Props do componente GradientText */
export interface GradientTextProps {
  /** Texto a ser exibido */
  children: string;
  /** Estilo de texto pré-definido (padrão: h2) */
  variant?: keyof typeof TextStyles;
  /** Estilos adicionais */
  style?: TextStyle;
  /** Identificador para testes */
  testID?: string;
}

/**
 * Texto estilizado com a cor primária da marca.
 *
 * Nota: Para gradiente real (verde→laranja), seria necessário
 * expo-linear-gradient + MaskedView. Aqui usamos a cor primária
 * como alternativa elegante e performática.
 */
export function GradientText({
  children,
  variant = 'h2',
  style,
  testID,
}: GradientTextProps): React.JSX.Element {
  const textStyle = TextStyles[variant];

  return (
    <Text
      testID={testID}
      style={[
        styles.text,
        textStyle,
        { color: BrandColors.primary },
        style,
      ]}
    >
      {children}
    </Text>
  );
}

const styles = StyleSheet.create({
  text: {
    fontFamily: FontFamily.bold,
  },
});

export default GradientText;
