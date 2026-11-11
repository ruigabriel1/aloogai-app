/**
 * TypingIndicator — Indicador de digitação do chat Aloogaí
 *
 * Exibe animação de 3 pontos pulsantes com o nome do
 * usuário que está digitando.
 *
 * Adapta automaticamente ao tema ativo (Light/Dark).
 */

import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { useTheme } from '../../theme';
import { FontFamily, FontSize } from '../../theme/typography';
import { Spacing, BorderRadius } from '../../theme/spacing';

/** Props do TypingIndicator */
export interface TypingIndicatorProps {
  /** Nome do usuário que está digitando */
  nome: string;
  /** Se o indicador está visível */
  visivel: boolean;
}

/** Indicador de digitação com animação de pontos */
export function TypingIndicator({
  nome,
  visivel,
}: TypingIndicatorProps): React.JSX.Element | null {
  const { colors } = useTheme();

  // Animações dos 3 pontos
  const dot1 = useRef(new Animated.Value(0)).current;
  const dot2 = useRef(new Animated.Value(0)).current;
  const dot3 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!visivel) return;

    // Cria animação pulsante para cada ponto com atraso escalonado
    const criarAnimacao = (dot: Animated.Value, delay: number) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(dot, {
            toValue: 1,
            duration: 400,
            useNativeDriver: true,
          }),
          Animated.timing(dot, {
            toValue: 0,
            duration: 400,
            useNativeDriver: true,
          }),
        ]),
      );

    const anim1 = criarAnimacao(dot1, 0);
    const anim2 = criarAnimacao(dot2, 200);
    const anim3 = criarAnimacao(dot3, 400);

    anim1.start();
    anim2.start();
    anim3.start();

    return () => {
      anim1.stop();
      anim2.stop();
      anim3.stop();
    };
  }, [visivel, dot1, dot2, dot3]);

  if (!visivel) return null;

  /** Renderiza um ponto animado */
  const renderDot = (animValue: Animated.Value) => (
    <Animated.View
      style={[
        styles.dot,
        { backgroundColor: colors.textTertiary },
        {
          transform: [
            {
              translateY: animValue.interpolate({
                inputRange: [0, 1],
                outputRange: [0, -4],
              }),
            },
          ],
          opacity: animValue.interpolate({
            inputRange: [0, 1],
            outputRange: [0.4, 1],
          }),
        },
      ]}
    />
  );

  return (
    <View style={styles.container}>
      <View
        style={[styles.bubble, { backgroundColor: colors.surfaceVariant }]}
      >
        <View style={styles.dotsContainer}>
          {renderDot(dot1)}
          {renderDot(dot2)}
          {renderDot(dot3)}
        </View>
      </View>
      <Text style={[styles.nome, { color: colors.textTertiary }]}>
        {nome} está digitando...
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    gap: Spacing.sm,
  },
  bubble: {
    paddingHorizontal: Spacing.ms,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.lg,
  },
  dotsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
  },
  nome: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.sm,
    fontStyle: 'italic',
  },
});

export default TypingIndicator;
