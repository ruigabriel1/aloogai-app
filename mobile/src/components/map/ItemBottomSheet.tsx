/**
 * ItemBottomSheet — Preview de item no mapa do Aloogaí
 *
 * BottomSheet com informações resumidas do item selecionado:
 * - Foto, título, preço, distância
 * - Dados do locador com avaliação
 * - Botão "Ver Detalhes"
 *
 * Animação suave de abertura com Animated API.
 * Adapta automaticamente ao tema ativo (Light/Dark).
 */

import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Image,
  TouchableOpacity,
  Animated,
  Dimensions,
} from 'react-native';
import { useTheme } from '../../theme';
import { TextStyles, FontFamily, FontSize } from '../../theme/typography';
import { Spacing, BorderRadius, Shadows } from '../../theme/spacing';
import { BrandColors } from '../../theme/colors';
import type { ItemProximidade } from '../../api/catalog';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

/** Props do ItemBottomSheet */
export interface ItemBottomSheetProps {
  /** Item selecionado no mapa */
  item: ItemProximidade | null;
  /** Se o sheet está visível */
  visivel: boolean;
  /** Callback ao pressionar "Ver Detalhes" */
  onVerDetalhes: (itemId: string) => void;
  /** Callback ao fechar o sheet */
  onFechar: () => void;
}

/**
 * BottomSheet animado com preview do item selecionado no mapa.
 */
export function ItemBottomSheet({
  item,
  visivel,
  onVerDetalhes,
  onFechar,
}: ItemBottomSheetProps): React.JSX.Element | null {
  const { colors, isDark } = useTheme();
  const translateY = useRef(new Animated.Value(300)).current;

  // Animação de entrada/saída
  useEffect(() => {
    Animated.spring(translateY, {
      toValue: visivel ? 0 : 300,
      useNativeDriver: true,
      tension: 65,
      friction: 11,
    }).start();
  }, [visivel, translateY]);

  if (!item) return null;

  /** Renderiza as estrelas de avaliação */
  const renderEstrelas = (nota: number) => {
    const estrelas: string[] = [];
    const notaArredondada = Math.round(nota * 2) / 2;

    for (let i = 1; i <= 5; i++) {
      if (i <= notaArredondada) {
        estrelas.push('★');
      } else if (i - 0.5 === notaArredondada) {
        estrelas.push('★');
      } else {
        estrelas.push('☆');
      }
    }

    return estrelas.join('');
  };

  /** Formata distância para exibição */
  const formatarDistancia = (km: number): string => {
    if (km < 1) {
      return `${Math.round(km * 1000)}m`;
    }
    return `${km.toFixed(1)}km`;
  };

  return (
    <Animated.View
      style={[
        styles.container,
        {
          transform: [{ translateY }],
        },
      ]}
    >
      {/* Overlay tocável para fechar */}
      <TouchableOpacity
        style={styles.overlay}
        activeOpacity={1}
        onPress={onFechar}
      />

      {/* Card do item */}
      <View
        style={[
          styles.card,
          {
            backgroundColor: colors.cardBackground,
            borderColor: colors.cardBorder,
          },
          !isDark && Shadows.lg,
        ]}
      >
        {/* Handle de arraste */}
        <View style={styles.handleContainer}>
          <View
            style={[styles.handle, { backgroundColor: colors.border }]}
          />
        </View>

        <View style={styles.conteudo}>
          {/* Foto do item */}
          <View style={styles.fotoContainer}>
            <Image
              source={
                item.foto_capa_url
                  ? { uri: item.foto_capa_url }
                  : undefined
              }
              style={[
                styles.foto,
                { backgroundColor: colors.surfaceVariant },
              ]}
              resizeMode="cover"
            />
            {!item.foto_capa_url && (
              <View style={styles.fotoPlaceholder}>
                <Text style={styles.fotoPlaceholderText}>📷</Text>
              </View>
            )}

            {/* Badge de destaque */}
            {item.is_destacado && (
              <View style={styles.destaqueBadge}>
                <Text style={styles.destaqueBadgeText}>⭐ Destaque</Text>
              </View>
            )}
          </View>

          {/* Informações do item */}
          <View style={styles.info}>
            {/* Título e preço */}
            <Text
              style={[styles.titulo, { color: colors.text }]}
              numberOfLines={2}
            >
              {item.titulo}
            </Text>

            <View style={styles.precoContainer}>
              <Text style={[styles.preco, { color: BrandColors.primary }]}>
                R$ {item.preco_diaria}
              </Text>
              <Text style={[styles.precoPeriodo, { color: colors.textSecondary }]}>
                /dia
              </Text>
            </View>

            {/* Distância e avaliação */}
            <View style={styles.metaContainer}>
              <View style={styles.metaItem}>
                <Text style={styles.metaIcone}>📍</Text>
                <Text style={[styles.metaTexto, { color: colors.textSecondary }]}>
                  {formatarDistancia(item.distancia_km)}
                </Text>
              </View>

              <View style={styles.metaItem}>
                <Text style={[styles.estrelas, { color: BrandColors.highlight }]}>
                  {renderEstrelas(item.avaliacao_media)}
                </Text>
                <Text style={[styles.metaTexto, { color: colors.textSecondary }]}>
                  {item.avaliacao_media.toFixed(1)}
                </Text>
              </View>
            </View>

            {/* Locador */}
            <View style={styles.locadorContainer}>
              <View
                style={[
                  styles.locadorAvatar,
                  { backgroundColor: BrandColors.primary },
                ]}
              >
                <Text style={styles.locadorAvatarText}>
                  {item.locador.nome.charAt(0).toUpperCase()}
                </Text>
              </View>
              <Text
                style={[styles.locadorNome, { color: colors.textSecondary }]}
                numberOfLines={1}
              >
                {item.locador.nome}
              </Text>
            </View>
          </View>
        </View>

        {/* Botão Ver Detalhes */}
        <TouchableOpacity
          style={styles.botaoDetalhes}
          activeOpacity={0.8}
          onPress={() => onVerDetalhes(item.id)}
        >
          <Text style={styles.botaoDetalhesTexto}>Ver Detalhes</Text>
        </TouchableOpacity>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    zIndex: 100,
  },
  overlay: {
    height: 20,
  },
  card: {
    borderTopLeftRadius: BorderRadius.xxl,
    borderTopRightRadius: BorderRadius.xxl,
    borderWidth: 1,
    borderBottomWidth: 0,
    paddingBottom: Spacing.lg,
  },
  handleContainer: {
    alignItems: 'center',
    paddingVertical: Spacing.sm,
  },
  handle: {
    width: 40,
    height: 4,
    borderRadius: BorderRadius.full,
  },
  conteudo: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.md,
    gap: Spacing.ms,
  },
  fotoContainer: {
    position: 'relative',
  },
  foto: {
    width: 110,
    height: 110,
    borderRadius: BorderRadius.md,
  },
  fotoPlaceholder: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: BorderRadius.md,
  },
  fotoPlaceholderText: {
    fontSize: 32,
  },
  destaqueBadge: {
    position: 'absolute',
    top: Spacing.xs,
    left: Spacing.xs,
    backgroundColor: BrandColors.highlight,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  destaqueBadgeText: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.xs,
    color: BrandColors.black,
  },
  info: {
    flex: 1,
    justifyContent: 'space-between',
  },
  titulo: {
    ...TextStyles.bodyBold,
    marginBottom: 2,
  },
  precoContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  preco: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.lg,
  },
  precoPeriodo: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.sm,
    marginLeft: 2,
  },
  metaContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaIcone: {
    fontSize: 12,
  },
  metaTexto: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.sm,
  },
  estrelas: {
    fontSize: FontSize.sm,
  },
  locadorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  locadorAvatar: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  locadorAvatarText: {
    fontFamily: FontFamily.bold,
    fontSize: 10,
    color: BrandColors.white,
  },
  locadorNome: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.sm,
    flex: 1,
  },
  botaoDetalhes: {
    marginHorizontal: Spacing.md,
    backgroundColor: BrandColors.primary,
    paddingVertical: Spacing.ms,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
  },
  botaoDetalhesTexto: {
    ...TextStyles.button,
    color: BrandColors.white,
  },
});

export default ItemBottomSheet;
