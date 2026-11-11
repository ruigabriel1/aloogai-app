/**
 * RentalsScreen — Lista de locações do Aloogaí
 *
 * Exibe locações do usuário com tabs:
 * - "Como Locatário" (itens que alugou)
 * - "Como Locador" (itens que alugou para outros)
 *
 * Cards com status colorido seguindo FSM:
 * SOLICITADO (amarelo), ATIVO (verde), DEVOLVIDO (azul),
 * CONCLUIDO (cinza), CONTESTADO (vermelho), CANCELADO (cinza escuro)
 *
 * Adapta automaticamente ao tema ativo (Light/Dark).
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from '../../theme';
import { TextStyles, FontFamily, FontSize } from '../../theme/typography';
import { Spacing, BorderRadius, Shadows } from '../../theme/spacing';
import { BrandColors } from '../../theme/colors';
import { listarLocacoes, type Locacao, type StatusLocacao } from '../../api/rentals';

/** Mapa de cores por status da locação */
const STATUS_CONFIG: Record<
  StatusLocacao,
  { cor: string; bg: string; label: string; icone: string }
> = {
  SOLICITADO: {
    cor: '#795548',
    bg: '#FFF8E1',
    label: 'Solicitado',
    icone: '⏳',
  },
  CAUCAO_RETIDA: {
    cor: '#F57C00',
    bg: '#FFF3E0',
    label: 'Caução Retida',
    icone: '🔒',
  },
  ATIVO: {
    cor: '#2E7D32',
    bg: '#E8F5E9',
    label: 'Ativo',
    icone: '✅',
  },
  DEVOLVIDO: {
    cor: '#1565C0',
    bg: '#E3F2FD',
    label: 'Devolvido',
    icone: '📦',
  },
  CONCLUIDO: {
    cor: '#616161',
    bg: '#F5F5F5',
    label: 'Concluído',
    icone: '✔️',
  },
  CANCELADO: {
    cor: '#9E9E9E',
    bg: '#EEEEEE',
    label: 'Cancelado',
    icone: '✕',
  },
  CONTESTADO: {
    cor: '#C62828',
    bg: '#FFEBEE',
    label: 'Contestado',
    icone: '⚠️',
  },
};

/** Tabs disponíveis */
type TabTipo = 'locatario' | 'locador';

/** Formata uma data ISO para DD/MM/AAAA */
function formatarData(iso: string): string {
  const data = new Date(iso);
  const dia = data.getDate().toString().padStart(2, '0');
  const mes = (data.getMonth() + 1).toString().padStart(2, '0');
  const ano = data.getFullYear();
  return `${dia}/${mes}/${ano}`;
}

/** Tela de Aluguéis */
export function RentalsScreen(): React.JSX.Element {
  const { colors, isDark } = useTheme();
  const [tabAtiva, setTabAtiva] = useState<TabTipo>('locatario');

  // Query de locações por tipo
  const {
    data: locacoes,
    isLoading,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['locacoes', tabAtiva],
    queryFn: () => listarLocacoes(tabAtiva),
  });

  /** Alterna entre tabs */
  const handleTabPress = useCallback((tab: TabTipo) => {
    setTabAtiva(tab);
  }, []);

  /** Renderiza um card de locação */
  const renderLocacao = ({ item: locacao }: { item: Locacao }) => {
    const statusConfig = STATUS_CONFIG[locacao.status];

    return (
      <View
        style={[
          styles.card,
          {
            backgroundColor: colors.cardBackground,
            borderColor: colors.cardBorder,
          },
          !isDark && Shadows.sm,
        ]}
      >
        {/* Foto e info principal */}
        <View style={styles.cardConteudo}>
          {/* Foto do item */}
          <View style={styles.cardFotoContainer}>
            {locacao.item.foto_capa_url ? (
              <Image
                source={{ uri: locacao.item.foto_capa_url }}
                style={[
                  styles.cardFoto,
                  { backgroundColor: colors.surfaceVariant },
                ]}
                resizeMode="cover"
              />
            ) : (
              <View
                style={[
                  styles.cardFoto,
                  styles.cardFotoPlaceholder,
                  { backgroundColor: colors.surfaceVariant },
                ]}
              >
                <Text style={styles.cardFotoPlaceholderTexto}>📦</Text>
              </View>
            )}
          </View>

          {/* Informações */}
          <View style={styles.cardInfo}>
            <Text
              style={[styles.cardTitulo, { color: colors.text }]}
              numberOfLines={2}
            >
              {locacao.item.titulo}
            </Text>

            {/* Datas */}
            <View style={styles.cardDatasRow}>
              <Text style={[styles.cardDatasTexto, { color: colors.textSecondary }]}>
                📅 {formatarData(locacao.data_inicio)} → {formatarData(locacao.data_fim)}
              </Text>
            </View>

            {/* Participante */}
            <Text
              style={[styles.cardParticipante, { color: colors.textTertiary }]}
              numberOfLines={1}
            >
              {tabAtiva === 'locatario'
                ? `🏠 ${locacao.item.locador.nome}`
                : `👤 ${locacao.locatario.nome}`}
            </Text>

            {/* Status badge */}
            <View
              style={[
                styles.statusBadge,
                { backgroundColor: isDark ? colors.surfaceVariant : statusConfig.bg },
              ]}
            >
              <Text style={styles.statusIcone}>{statusConfig.icone}</Text>
              <Text
                style={[
                  styles.statusTexto,
                  { color: statusConfig.cor },
                ]}
              >
                {statusConfig.label}
              </Text>
            </View>
          </View>
        </View>

        {/* Rodapé com valor */}
        <View style={[styles.cardRodape, { borderTopColor: colors.border }]}>
          <Text style={[styles.cardValorLabel, { color: colors.textSecondary }]}>
            Total
          </Text>
          <Text style={[styles.cardValor, { color: BrandColors.primary }]}>
            R$ {locacao.valor_total}
          </Text>
        </View>
      </View>
    );
  };

  /** Renderiza estado vazio */
  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      <View
        style={[
          styles.emptyIconeContainer,
          { backgroundColor: colors.surfaceVariant },
        ]}
      >
        <Text style={styles.emptyIcone}>
          {tabAtiva === 'locatario' ? '🛒' : '📋'}
        </Text>
      </View>
      <Text style={[styles.emptyTitulo, { color: colors.text }]}>
        {tabAtiva === 'locatario'
          ? 'Nenhum aluguel ainda'
          : 'Nenhuma locação como locador'}
      </Text>
      <Text style={[styles.emptySubtitulo, { color: colors.textSecondary }]}>
        {tabAtiva === 'locatario'
          ? 'Explore o mapa e alugue itens\nda sua vizinhança!'
          : 'Publique itens e comece\na receber locações!'}
      </Text>
    </View>
  );

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.headerTitulo, { color: colors.text }]}>
          Aluguéis
        </Text>
      </View>

      {/* Tabs */}
      <View
        style={[styles.tabsContainer, { borderBottomColor: colors.border }]}
      >
        <TouchableOpacity
          style={[
            styles.tab,
            tabAtiva === 'locatario' && [
              styles.tabAtiva,
              { borderBottomColor: BrandColors.primary },
            ],
          ]}
          activeOpacity={0.7}
          onPress={() => handleTabPress('locatario')}
        >
          <Text
            style={[
              styles.tabTexto,
              {
                color:
                  tabAtiva === 'locatario'
                    ? BrandColors.primary
                    : colors.textTertiary,
              },
            ]}
          >
            Como Locatário
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.tab,
            tabAtiva === 'locador' && [
              styles.tabAtiva,
              { borderBottomColor: BrandColors.primary },
            ],
          ]}
          activeOpacity={0.7}
          onPress={() => handleTabPress('locador')}
        >
          <Text
            style={[
              styles.tabTexto,
              {
                color:
                  tabAtiva === 'locador'
                    ? BrandColors.primary
                    : colors.textTertiary,
              },
            ]}
          >
            Como Locador
          </Text>
        </TouchableOpacity>
      </View>

      {/* Lista de locações */}
      {isLoading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={BrandColors.primary} />
          <Text style={[styles.loadingTexto, { color: colors.textSecondary }]}>
            Carregando aluguéis...
          </Text>
        </View>
      ) : (
        <FlatList
          data={locacoes || []}
          renderItem={renderLocacao}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listaConteudo}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={renderEmpty}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={() => refetch()}
              colors={[BrandColors.primary]}
              tintColor={BrandColors.primary}
            />
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
  },
  header: {
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.md,
    paddingBottom: Spacing.sm,
  },
  headerTitulo: {
    ...TextStyles.h1,
  },
  tabsContainer: {
    flexDirection: 'row',
    borderBottomWidth: 1,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: Spacing.ms,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabAtiva: {
    borderBottomWidth: 2,
  },
  tabTexto: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.md,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.md,
  },
  loadingTexto: {
    ...TextStyles.body,
  },
  listaConteudo: {
    padding: Spacing.md,
    paddingBottom: Spacing.xxl,
    flexGrow: 1,
  },
  card: {
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    marginBottom: Spacing.md,
    overflow: 'hidden',
  },
  cardConteudo: {
    flexDirection: 'row',
    padding: Spacing.md,
    gap: Spacing.ms,
  },
  cardFotoContainer: {
    borderRadius: BorderRadius.md,
    overflow: 'hidden',
  },
  cardFoto: {
    width: 80,
    height: 80,
    borderRadius: BorderRadius.md,
  },
  cardFotoPlaceholder: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardFotoPlaceholderTexto: {
    fontSize: 28,
  },
  cardInfo: {
    flex: 1,
    justifyContent: 'space-between',
  },
  cardTitulo: {
    ...TextStyles.bodyBold,
    marginBottom: 4,
  },
  cardDatasRow: {
    marginBottom: 4,
  },
  cardDatasTexto: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.sm,
  },
  cardParticipante: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.sm,
    marginBottom: 6,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    borderRadius: BorderRadius.sm,
    gap: 4,
  },
  statusIcone: {
    fontSize: 12,
  },
  statusTexto: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.xs,
  },
  cardRodape: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderTopWidth: 1,
  },
  cardValorLabel: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.sm,
  },
  cardValor: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.base,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.huge,
    paddingHorizontal: Spacing.xl,
  },
  emptyIconeContainer: {
    width: 88,
    height: 88,
    borderRadius: 44,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.lg,
  },
  emptyIcone: {
    fontSize: 40,
  },
  emptyTitulo: {
    ...TextStyles.h3,
    marginBottom: Spacing.sm,
    textAlign: 'center',
  },
  emptySubtitulo: {
    ...TextStyles.body,
    textAlign: 'center',
    lineHeight: 22,
  },
});

export default RentalsScreen;
