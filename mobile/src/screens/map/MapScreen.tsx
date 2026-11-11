/**
 * MapScreen — Tela principal do Aloogaí (Mapa de Proximidade)
 *
 * Tela principal do app com mapa real de itens disponíveis:
 * - MapView com markers dos itens da API
 * - Barra de busca com filtros no topo
 * - Chips de categorias scrollable
 * - Botão de centralizar localização
 * - FAB "Publicar item"
 * - BottomSheet de preview ao tocar num marker
 *
 * Adapta automaticamente ao tema ativo (Light/Dark).
 */

import React, { useState, useRef, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Platform,
  Dimensions,
  Alert,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import MapView, { PROVIDER_GOOGLE, type Region } from 'react-native-maps';
import { useQuery } from '@tanstack/react-query';
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
import { ItemMarker } from '../../components/map/ItemMarker';
import { ItemBottomSheet } from '../../components/map/ItemBottomSheet';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { MainStackParamList } from '../../navigation/types';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

/** Raio padrão de busca em km */
const RAIO_PADRAO_KM = 5;

/** Estilo do mapa para Dark Mode */
const MAP_DARK_STYLE = [
  { elementType: 'geometry', stylers: [{ color: '#242f3e' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#242f3e' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#746855' }] },
  {
    featureType: 'administrative.locality',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#d59563' }],
  },
  {
    featureType: 'poi',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#d59563' }],
  },
  {
    featureType: 'poi.park',
    elementType: 'geometry',
    stylers: [{ color: '#263c3f' }],
  },
  {
    featureType: 'road',
    elementType: 'geometry',
    stylers: [{ color: '#38414e' }],
  },
  {
    featureType: 'road',
    elementType: 'geometry.stroke',
    stylers: [{ color: '#212a37' }],
  },
  {
    featureType: 'road.highway',
    elementType: 'geometry',
    stylers: [{ color: '#746855' }],
  },
  {
    featureType: 'water',
    elementType: 'geometry',
    stylers: [{ color: '#17263c' }],
  },
  {
    featureType: 'water',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#515c6d' }],
  },
];

/** Tela do Mapa de Proximidade */
export function MapScreen(): React.JSX.Element {
  const { colors, isDark } = useTheme();
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<NativeStackNavigationProp<MainStackParamList>>();
  const mapRef = useRef<MapView>(null);

  // Localização do usuário
  const { latitude, longitude, loading: locationLoading, refresh: refreshLocation } = useLocation();

  // Estado local
  const [textoBusca, setTextoBusca] = useState('');
  const [categoriaAtiva, setCategoriaAtiva] = useState<string | null>(null);
  const [itemSelecionado, setItemSelecionado] = useState<ItemProximidade | null>(null);
  const [bottomSheetVisivel, setBottomSheetVisivel] = useState(false);
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
  } = useQuery({
    queryKey: ['itens-proximidade', latitude, longitude, raioKm, filtros],
    queryFn: async () => {
      const data = await buscarItensProximidade(latitude, longitude, raioKm, filtros);
      return data || { type: 'FeatureCollection', features: [] };
    },
    enabled: !locationLoading,
    staleTime: 2 * 60 * 1000, // 2 minutos
  });

  // Query de categorias
  const { data: categorias } = useQuery({
    queryKey: ['categorias'],
    queryFn: async () => {
      const data = await buscarCategorias();
      return data || [];
    },
    staleTime: 10 * 60 * 1000, // 10 minutos
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

  /** Centraliza o mapa na posição do usuário */
  const centralizarMapa = useCallback(() => {
    mapRef.current?.animateToRegion(
      {
        latitude,
        longitude,
        latitudeDelta: 0.02,
        longitudeDelta: 0.02,
      },
      500,
    );
  }, [latitude, longitude]);

  /** Seleciona um item no mapa */
  const selecionarItem = useCallback((item: ItemProximidade) => {
    setItemSelecionado(item);
    setBottomSheetVisivel(true);

    // Centraliza o mapa no item selecionado
    mapRef.current?.animateToRegion(
      {
        latitude: item.latitude,
        longitude: item.longitude,
        latitudeDelta: 0.01,
        longitudeDelta: 0.01,
      },
      400,
    );
  }, []);

  /** Fecha o BottomSheet */
  const fecharBottomSheet = useCallback(() => {
    setBottomSheetVisivel(false);
    setItemSelecionado(null);
  }, []);

  /** Navega para detalhes do item */
  const irParaDetalhes = useCallback(
    (itemId: string) => {
      fecharBottomSheet();
      navigation.navigate('ItemDetalhe', { itemId });
    },
    [navigation, fecharBottomSheet],
  );

  /** Seleciona/deseleciona uma categoria */
  const toggleCategoria = useCallback(
    (categoriaId: string) => {
      setCategoriaAtiva((prev) => (prev === categoriaId ? null : categoriaId));
    },
    [],
  );

  /** Navega para publicação de item */
  const irParaPublicar = useCallback(() => {
    navigation.navigate('CreateItem');
  }, [navigation]);

  /** Região inicial do mapa */
  const regiao: Region = {
    latitude,
    longitude,
    latitudeDelta: 0.02,
    longitudeDelta: 0.02,
  };

  return (
    <View style={styles.flex}>
      {/* Mapa ocupando tela toda */}
      <MapView
        ref={mapRef}
        style={styles.mapa}
        provider={Platform.OS === 'android' ? PROVIDER_GOOGLE : undefined}
        initialRegion={regiao}
        showsUserLocation
        showsMyLocationButton={false}
        showsCompass={false}
        customMapStyle={isDark ? MAP_DARK_STYLE : undefined}
        onPress={fecharBottomSheet}
      >
        {/* Markers dos itens */}
        {itens.map((item) => (
          <ItemMarker
            key={item.id}
            identifier={item.id}
            coordinate={{
              latitude: item.latitude,
              longitude: item.longitude,
            }}
            titulo={item.titulo}
            precoDiaria={item.preco_diaria}
            isDestacado={item.is_destacado}
            categoriaIcone={item.categoria?.icone}
            onPress={() => selecionarItem(item)}
          />
        ))}
      </MapView>

      {/* Overlay de busca no topo */}
      <SafeAreaView
        style={styles.topOverlay}
        edges={['top']}
      >
        {navigation.canGoBack() && (
          <TouchableOpacity 
            style={[styles.backBotao, { backgroundColor: colors.cardBackground }, !isDark && Shadows.sm]} 
            onPress={() => navigation.goBack()}
          >
            <Text style={[styles.backTexto, { color: colors.text }]}>← Fechar Mapa</Text>
          </TouchableOpacity>
        )}
        {/* Barra de busca */}
        <View
          style={[
            styles.searchContainer,
            {
              backgroundColor: colors.cardBackground,
              borderColor: colors.cardBorder,
            },
            !isDark && Shadows.md,
          ]}
        >
          <Text style={styles.searchIcone}>🔍</Text>
          <TextInput
            style={[
              styles.searchInput,
              { color: colors.text },
            ]}
            placeholder="Buscar itens na vizinhança..."
            placeholderTextColor={colors.inputPlaceholder}
            value={textoBusca}
            onChangeText={setTextoBusca}
            returnKeyType="search"
            onSubmitEditing={() => refetchItens()}
          />
          {textoBusca.length > 0 && (
            <TouchableOpacity
              onPress={() => setTextoBusca('')}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
              <Text style={[styles.clearTexto, { color: colors.textTertiary }]}>
                ✕
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Chips de categorias */}
        {categorias && categorias.length > 0 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.categoriasContainer}
            style={styles.categoriasScroll}
          >
            {/* Chip "Todos" */}
            <TouchableOpacity
              style={[
                styles.categoriaChip,
                {
                  backgroundColor: !categoriaAtiva
                    ? BrandColors.primary
                    : colors.cardBackground,
                  borderColor: !categoriaAtiva
                    ? BrandColors.primary
                    : colors.cardBorder,
                },
                !isDark && !categoriaAtiva && Shadows.sm,
              ]}
              activeOpacity={0.7}
              onPress={() => setCategoriaAtiva(null)}
            >
              <Text
                style={[
                  styles.categoriaChipTexto,
                  {
                    color: !categoriaAtiva
                      ? BrandColors.white
                      : colors.text,
                  },
                ]}
              >
                📋 Todos
              </Text>
            </TouchableOpacity>

            {categorias.map((cat) => (
              <TouchableOpacity
                key={cat.id}
                style={[
                  styles.categoriaChip,
                  {
                    backgroundColor:
                      categoriaAtiva === cat.id
                        ? BrandColors.primary
                        : colors.cardBackground,
                    borderColor:
                      categoriaAtiva === cat.id
                        ? BrandColors.primary
                        : colors.cardBorder,
                  },
                  !isDark && Shadows.sm,
                ]}
                activeOpacity={0.7}
                onPress={() => toggleCategoria(cat.id)}
              >
                <Text
                  style={[
                    styles.categoriaChipTexto,
                    {
                      color:
                        categoriaAtiva === cat.id
                          ? BrandColors.white
                          : colors.text,
                    },
                  ]}
                >
                  {cat.icone} {cat.nome}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}

        {/* Indicador de carregamento */}
        {(itensLoading || locationLoading) && (
          <View
            style={[
              styles.loadingBadge,
              { backgroundColor: colors.cardBackground },
              !isDark && Shadows.sm,
            ]}
          >
            <ActivityIndicator size="small" color={BrandColors.primary} />
            <Text style={[styles.loadingTexto, { color: colors.textSecondary }]}>
              {locationLoading ? 'Obtendo localização...' : 'Buscando itens...'}
            </Text>
          </View>
        )}
      </SafeAreaView>

      {/* Botão centralizar localização */}
      <TouchableOpacity
        style={[
          styles.botaoCentralizar,
          {
            backgroundColor: colors.cardBackground,
            borderColor: colors.cardBorder,
            bottom: bottomSheetVisivel ? 280 : 100,
          },
          !isDark && Shadows.md,
        ]}
        activeOpacity={0.7}
        onPress={() => {
          refreshLocation();
          centralizarMapa();
        }}
      >
        <Text style={styles.botaoCentralizarIcone}>📍</Text>
      </TouchableOpacity>

      {/* Contador de itens */}
      {!itensLoading && itens.length > 0 && (
        <View
          style={[
            styles.contadorItens,
            {
              backgroundColor: colors.cardBackground,
              borderColor: colors.cardBorder,
              bottom: bottomSheetVisivel ? 280 : 100,
            },
            !isDark && Shadows.sm,
          ]}
        >
          <Text style={[styles.contadorTexto, { color: colors.text }]}>
            {itens.length} {itens.length === 1 ? 'item' : 'itens'}
          </Text>
          <Text style={[styles.contadorSub, { color: colors.textSecondary }]}>
            em {raioKm}km
          </Text>
        </View>
      )}

      {/* FAB — Publicar item */}
      <TouchableOpacity
        style={[
          styles.fab,
          { bottom: bottomSheetVisivel ? 280 : 100 },
          Shadows.lg,
        ]}
        activeOpacity={0.8}
        onPress={irParaPublicar}
      >
        <Text style={styles.fabIcone}>＋</Text>
        <Text style={styles.fabTexto}>Publicar</Text>
      </TouchableOpacity>

      {/* BottomSheet de preview */}
      <ItemBottomSheet
        item={itemSelecionado}
        visivel={bottomSheetVisivel}
        onVerDetalhes={irParaDetalhes}
        onFechar={fecharBottomSheet}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },
  mapa: {
    ...StyleSheet.absoluteFillObject,
  },
  topOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 10,
  },
  backBotao: {
    alignSelf: 'flex-start',
    marginLeft: Spacing.md,
    marginTop: Spacing.sm,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.full,
  },
  backTexto: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.sm,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: Spacing.md,
    marginTop: Spacing.sm,
    paddingHorizontal: Spacing.md,
    paddingVertical: Platform.OS === 'ios' ? Spacing.ms : Spacing.sm,
    borderRadius: BorderRadius.xl,
    borderWidth: 1,
    gap: Spacing.sm,
  },
  searchIcone: {
    fontSize: 18,
  },
  searchInput: {
    flex: 1,
    fontFamily: FontFamily.regular,
    fontSize: FontSize.base,
    padding: 0,
  },
  clearTexto: {
    fontSize: 16,
    fontFamily: FontFamily.medium,
  },
  categoriasScroll: {
    marginTop: Spacing.sm,
  },
  categoriasContainer: {
    paddingHorizontal: Spacing.md,
    gap: Spacing.sm,
  },
  categoriaChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.ms,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
  },
  categoriaChipTexto: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.sm,
  },
  loadingBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'center',
    marginTop: Spacing.sm,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.full,
    gap: Spacing.sm,
  },
  loadingTexto: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.sm,
  },
  botaoCentralizar: {
    position: 'absolute',
    right: Spacing.md,
    width: 48,
    height: 48,
    borderRadius: 24,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  botaoCentralizarIcone: {
    fontSize: 22,
  },
  contadorItens: {
    position: 'absolute',
    left: Spacing.md,
    paddingHorizontal: Spacing.ms,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    alignItems: 'center',
  },
  contadorTexto: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.md,
  },
  contadorSub: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.xs,
  },
  fab: {
    position: 'absolute',
    right: Spacing.md,
    backgroundColor: BrandColors.primary,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.ms,
    borderRadius: BorderRadius.full,
    gap: Spacing.xs,
  },
  fabIcone: {
    fontSize: 20,
    color: BrandColors.white,
    fontFamily: FontFamily.bold,
  },
  fabTexto: {
    ...TextStyles.buttonSmall,
    color: BrandColors.white,
  },
});

export default MapScreen;
