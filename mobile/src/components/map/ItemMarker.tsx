/**
 * ItemMarker — Marker customizado no mapa do Aloogaí
 *
 * Exibe markers com cores diferenciadas:
 * - Verde: itens normais
 * - Amarelo/Dourado: itens destacados (impulsionados)
 *
 * Adapta automaticamente ao tema ativo (Light/Dark).
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Marker } from 'react-native-maps';
import { useTheme } from '../../theme';
import { BrandColors } from '../../theme/colors';
import { FontFamily, FontSize } from '../../theme/typography';
import { BorderRadius, Spacing } from '../../theme/spacing';

/** Props do ItemMarker */
export interface ItemMarkerProps {
  /** Coordenadas do marker */
  coordinate: {
    latitude: number;
    longitude: number;
  };
  /** Título do item (tooltip) */
  titulo: string;
  /** Preço por diária formatado */
  precoDiaria: string;
  /** Se o item é destacado (impulsionado) */
  isDestacado?: boolean;
  /** Ícone da categoria (emoji) */
  categoriaIcone?: string;
  /** Callback ao pressionar o marker */
  onPress?: () => void;
  /** Identificador único */
  identifier?: string;
}

/**
 * Marker customizado para exibir itens no mapa.
 *
 * Itens destacados possuem borda dourada e fundo amarelo.
 * Itens normais possuem fundo verde da marca.
 */
export function ItemMarker({
  coordinate,
  titulo,
  precoDiaria,
  isDestacado = false,
  categoriaIcone = '📦',
  onPress,
  identifier,
}: ItemMarkerProps): React.JSX.Element {
  const { colors } = useTheme();

  const bgColor = isDestacado
    ? BrandColors.highlight
    : BrandColors.primary;

  const textColor = isDestacado
    ? BrandColors.black
    : BrandColors.white;

  const borderColor = isDestacado
    ? BrandColors.highlightDark
    : BrandColors.primaryDark;

  return (
    <Marker
      coordinate={coordinate}
      title={titulo}
      onPress={onPress}
      identifier={identifier}
      tracksViewChanges={false}
    >
      <View style={styles.container}>
        {/* Pin customizado */}
        <View
          style={[
            styles.pin,
            {
              backgroundColor: bgColor,
              borderColor: borderColor,
            },
          ]}
        >
          <Text style={styles.icone}>{categoriaIcone}</Text>
          <Text
            style={[styles.preco, { color: textColor }]}
            numberOfLines={1}
          >
            R${precoDiaria}
          </Text>
        </View>

        {/* Seta do pin */}
        <View
          style={[
            styles.seta,
            { borderTopColor: bgColor },
          ]}
        />

        {/* Indicador de destaque */}
        {isDestacado && (
          <View style={styles.destaqueContainer}>
            <Text style={styles.destaqueStar}>⭐</Text>
          </View>
        )}
      </View>
    </Marker>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
  },
  pin: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    borderRadius: BorderRadius.lg,
    borderWidth: 2,
    gap: 4,
    minWidth: 60,
  },
  icone: {
    fontSize: 14,
  },
  preco: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.xs,
  },
  seta: {
    width: 0,
    height: 0,
    borderLeftWidth: 6,
    borderRightWidth: 6,
    borderTopWidth: 8,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    marginTop: -1,
  },
  destaqueContainer: {
    position: 'absolute',
    top: -8,
    right: -8,
  },
  destaqueStar: {
    fontSize: 14,
  },
});

export default ItemMarker;
