/**
 * FeedScreen — Tela Inicial do Aloogaí (Lista de Itens)
 *
 * Tela principal do app em formato de Feed (estilo Mercado Livre):
 * - Header com cor primária e botão de Mapa
 * - Barra de busca com filtros no topo
 * - Chips de categorias scrollable
 * - Lista (FlatList) de itens próximos
 *
 * Adapta automaticamente ao tema ativo (Light/Dark).
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  FlatList,
  Platform,
  Dimensions,
  Image,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { MainStackParamList } from '../../navigation/types';

import { useTheme } from '../../theme';
import { TextStyles, FontFamily, FontSize } from '../../theme/typography';
import { Spacing, BorderRadius, Shadows } from '../../theme/spacing';
import { BrandColors } from '../../theme/colors';
import { useLocation } from '../../hooks/useLocation';
import {
  buscarItensProximidade,
  buscarCategorias,
  type ItemProximidade,
  type FiltrosBusca,
} from '../../api/catalog';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const RAIO_PADRAO_KM = 5;

export function FeedScreen(): React.JSX.Element {
  const { colors, isDark } = useTheme();
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<NativeStackNavigationProp<MainStackParamList>>();

  // Localização do usuário
  const { latitude, longitude, loading: locationLoading, permissaoConcedida } = useLocation();

  // Estado local
  const [textoBusca, setTextoBusca] = useState('');
  const [categoriaAtiva, setCategoriaAtiva] = useState<string | null>(null);
  const [raioKm] = useState(RAIO_PADRAO_KM);

  // Filtros de busca
  const filtros = useMemo<FiltrosBusca>(
    () => ({
      categoria_id: categoriaAtiva,
      q: textoBusca || undefined,
    }),
    [categoriaAtiva, textoBusca],
  );

  // Query de itens por proximidade
  const {
    data: itensData,
    isLoading: itensLoading,
    refetch: refetchItens,
    isError,
  } = useQuery({
    queryKey: ['itens-proximidade', latitude, longitude, raioKm, filtros],
    queryFn: async () => {
      const data = await buscarItensProximidade(latitude, longitude, raioKm, filtros);
      return data || { type: 'FeatureCollection', features: [] };
    },
    enabled: !locationLoading,
    staleTime: 2 * 60 * 1000,
  });

  // Query de categorias
  const { data: categorias } = useQuery({
    queryKey: ['categorias'],
    queryFn: async () => {
      const data = await buscarCategorias();
      return data || [];
    },
    staleTime: 10 * 60 * 1000,
  });

  // Extrai itens do GeoJSON
  const itens = useMemo<ItemProximidade[]>(() => {
    if (!itensData?.features) return [];
    return itensData.features.map((feature) => ({
      ...feature.properties,
      latitude: feature.geometry.coordinates[1],
      longitude: feature.geometry.coordinates[0],
    }));
  }, [itensData]);

  const toggleCategoria = useCallback((categoriaId: string) => {
    setCategoriaAtiva((prev) => (prev === categoriaId ? null : categoriaId));
  }, []);

  const irParaMapa = useCallback(() => {
    navigation.navigate('MapModal');
  }, [navigation]);

  const renderItemCard = ({ item }: { item: ItemProximidade }) => (
    <TouchableOpacity
      style={[
        styles.cardContainer,
        { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder },
        !isDark && Shadows.sm,
      ]}
      onPress={() => navigation.navigate('ItemDetalhe', { itemId: item.id })}
      activeOpacity={0.8}
    >
      <View style={styles.cardImagemContainer}>
        {item.foto_capa_url ? (
          <Image source={{ uri: item.foto_capa_url }} style={styles.cardImagem} />
        ) : (
          <View style={[styles.cardImagemPlaceholder, { backgroundColor: colors.background }]}>
            <Text style={{ fontSize: 32 }}>{item.categoria?.icone || '📦'}</Text>
          </View>
        )}
        {item.is_destacado && (
          <View style={styles.badgeDestaque}>
            <Text style={styles.badgeDestaqueTexto}>PRO</Text>
          </View>
        )}
      </View>
      <View style={styles.cardContent}>
        <Text style={[styles.cardTitulo, { color: colors.text }]} numberOfLines={2}>
          {item.titulo}
        </Text>
        <Text style={[styles.cardPreco, { color: BrandColors.primary }]}>
          R$ {item.preco_diaria}<Text style={styles.cardPrecoSufixo}>/dia</Text>
        </Text>
        <View style={styles.cardRodape}>
          <Text style={[styles.cardDistancia, { color: colors.textSecondary }]}>
            📍 {item.distancia_km.toFixed(1)} km
          </Text>
          {item.avaliacao_media && (
            <Text style={[styles.cardAvaliacao, { color: colors.textSecondary }]}>
              ⭐ {item.avaliacao_media.toFixed(1)}
            </Text>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Alerta de GPS caso permissão negada */}
      {!permissaoConcedida && !locationLoading && (
        <View style={{ backgroundColor: '#FFCC00', padding: Spacing.sm, paddingTop: insets.top + Spacing.sm, alignItems: 'center' }}>
          <Text style={{ fontFamily: FontFamily.semiBold, color: '#333' }}>
            📍 Usando São Paulo como padrão (GPS desligado)
          </Text>
        </View>
      )}

      {/* Header Estilo Mercado Livre */}
      <View style={[styles.headerContainer, { paddingTop: permissaoConcedida ? insets.top + Spacing.sm : Spacing.sm }]}>
        <View style={styles.headerTopRow}>
          {/* Barra de Busca */}
          <View style={styles.searchWrapper}>
            <Text style={styles.searchIcone}>🔍</Text>
            <TextInput
              style={styles.searchInput}
              placeholder="Buscar na vizinhança..."
              placeholderTextColor="#7f8c8d"
              value={textoBusca}
              onChangeText={setTextoBusca}
              returnKeyType="search"
              onSubmitEditing={() => refetchItens()}
              autoCapitalize="none"
              autoCorrect={false}
            />
            {textoBusca.length > 0 && (
              <TouchableOpacity onPress={() => setTextoBusca('')} style={styles.clearBotao}>
                <Text style={styles.clearTexto}>✕</Text>
              </TouchableOpacity>
            )}
          </View>

          {/* Botão de Mapa */}
          <TouchableOpacity style={styles.mapaBotao} onPress={irParaMapa} activeOpacity={0.7}>
            <Text style={styles.mapaIcone}>🗺️</Text>
            <Text style={styles.mapaTexto}>Mapa</Text>
          </TouchableOpacity>
        </View>

        {/* Chips de Categorias */}
        {categorias && categorias.length > 0 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.categoriasContainer}
            style={styles.categoriasScroll}
          >
            <TouchableOpacity
              style={[
                styles.categoriaChip,
                !categoriaAtiva ? styles.categoriaChipAtiva : styles.categoriaChipInativa,
              ]}
              onPress={() => setCategoriaAtiva(null)}
            >
              <Text style={!categoriaAtiva ? styles.chipTextoAtivo : styles.chipTextoInativo}>
                📋 Todos
              </Text>
            </TouchableOpacity>

            {categorias.map((cat) => (
              <TouchableOpacity
                key={cat.id}
                style={[
                  styles.categoriaChip,
                  categoriaAtiva === cat.id ? styles.categoriaChipAtiva : styles.categoriaChipInativa,
                ]}
                onPress={() => toggleCategoria(cat.id)}
              >
                <Text style={categoriaAtiva === cat.id ? styles.chipTextoAtivo : styles.chipTextoInativo}>
                  {cat.icone} {cat.nome}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}
      </View>

      {/* Loading / Lista de Itens */}
      {(locationLoading || itensLoading) ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={BrandColors.primary} />
          <Text style={[styles.loadingTexto, { color: colors.textSecondary }]}>
            {locationLoading ? 'Localizando você...' : 'Buscando itens próximos...'}
          </Text>
        </View>
      ) : isError ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>⚠️</Text>
          <Text style={[styles.emptyTexto, { color: colors.textSecondary }]}>
            Ocorreu um erro ao buscar os itens. Tente novamente.
          </Text>
        </View>
      ) : itens.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>🏜️</Text>
          <Text style={[styles.emptyTexto, { color: colors.textSecondary }]}>
            Nenhum item encontrado num raio de {raioKm}km.
          </Text>
        </View>
      ) : (
        <FlatList
          data={itens}
          keyExtractor={(item) => item.id}
          renderItem={renderItemCard}
          contentContainerStyle={styles.listaContainer}
          showsVerticalScrollIndicator={false}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  headerContainer: {
    backgroundColor: BrandColors.primary,
    paddingBottom: Spacing.sm,
  },
  headerTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    gap: Spacing.sm,
  },
  searchWrapper: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderRadius: BorderRadius.full,
    paddingHorizontal: Spacing.md,
    height: 44,
  },
  searchIcone: {
    fontSize: 16,
    marginRight: Spacing.xs,
  },
  searchInput: {
    flex: 1,
    fontFamily: FontFamily.regular,
    fontSize: FontSize.base,
    color: '#333333',
    padding: 0,
    height: '100%',
  },
  clearBotao: {
    padding: Spacing.xs,
  },
  clearTexto: {
    color: '#999',
    fontSize: 14,
    fontFamily: FontFamily.medium,
  },
  mapaBotao: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  mapaIcone: {
    fontSize: 20,
  },
  mapaTexto: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.xs,
    color: BrandColors.white,
    marginTop: 2,
  },
  categoriasScroll: {
    marginTop: Spacing.md,
  },
  categoriasContainer: {
    paddingHorizontal: Spacing.md,
    gap: Spacing.sm,
  },
  categoriaChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs + 2,
    borderRadius: BorderRadius.full,
  },
  categoriaChipAtiva: {
    backgroundColor: BrandColors.white,
  },
  categoriaChipInativa: {
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  chipTextoAtivo: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.sm,
    color: BrandColors.primary,
  },
  chipTextoInativo: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.sm,
    color: BrandColors.white,
  },
  listaContainer: {
    padding: Spacing.md,
    gap: Spacing.md,
  },
  cardContainer: {
    flexDirection: 'row',
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    overflow: 'hidden',
    height: 120,
  },
  cardImagemContainer: {
    width: 120,
    height: '100%',
    position: 'relative',
  },
  cardImagem: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  cardImagemPlaceholder: {
    width: '100%',
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeDestaque: {
    position: 'absolute',
    top: Spacing.xs,
    left: Spacing.xs,
    backgroundColor: BrandColors.accent,
    paddingHorizontal: Spacing.xs,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  badgeDestaqueTexto: {
    fontFamily: FontFamily.bold,
    fontSize: 10,
    color: '#000',
  },
  cardContent: {
    flex: 1,
    padding: Spacing.sm,
    justifyContent: 'space-between',
  },
  cardTitulo: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.md,
    lineHeight: 20,
  },
  cardPreco: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.lg,
    marginTop: Spacing.xs,
  },
  cardPrecoSufixo: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.xs,
  },
  cardRodape: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardDistancia: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.xs,
  },
  cardAvaliacao: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.xs,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingTexto: {
    marginTop: Spacing.sm,
    fontFamily: FontFamily.medium,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.xl,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: Spacing.md,
  },
  emptyTexto: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.md,
    textAlign: 'center',
    lineHeight: 22,
  },
});

export default FeedScreen;
