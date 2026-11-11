import React from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, ActivityIndicator, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { MainStackParamList } from '../../navigation/types';

import { useTheme } from '../../theme';
import { TextStyles, FontFamily, FontSize } from '../../theme/typography';
import { Spacing, BorderRadius, Shadows } from '../../theme/spacing';
import { BrandColors } from '../../theme/colors';
import { buscarMeusItens } from '../../api/catalog';
import { Button } from '../../components/ui/Button';

export function MyItemsScreen(): React.JSX.Element {
  const { colors, isDark } = useTheme();
  const navigation = useNavigation<NativeStackNavigationProp<MainStackParamList>>();

  const {
    data: itens,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['meus-itens'],
    queryFn: buscarMeusItens,
    staleTime: 60 * 1000,
  });

  const renderItemCard = ({ item }: { item: any }) => (
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
        {item.fotos && item.fotos.length > 0 ? (
          <Image source={{ uri: item.fotos[0].url }} style={styles.cardImagem} />
        ) : (
          <View style={[styles.cardImagemPlaceholder, { backgroundColor: colors.surfaceVariant }]}>
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
        <View>
          <Text style={[styles.cardTitulo, { color: colors.text }]} numberOfLines={2}>
            {item.titulo}
          </Text>
          <Text style={[styles.cardPreco, { color: BrandColors.primary }]}>
            R$ {item.preco_diaria}<Text style={styles.cardPrecoSufixo}>/dia</Text>
          </Text>
        </View>
        <View style={styles.cardRodape}>
          <Text style={[styles.status, { color: item.aprovado_para_uso ? BrandColors.success : BrandColors.highlight }]}>
            {item.aprovado_para_uso ? '✅ Ativo' : '⏳ Pendente'}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top', 'bottom']}>
      <View style={[styles.header, { borderBottomColor: colors.border }]}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Text style={[styles.backIcon, { color: colors.text }]}>←</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.text }]}>Meus Itens</Text>
        <View style={{ width: 24 }} />
      </View>

      {isLoading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color={BrandColors.primary} />
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>Buscando seus itens...</Text>
        </View>
      ) : isError ? (
        <View style={styles.centerContainer}>
          <Text style={{ fontSize: 48, marginBottom: Spacing.md }}>⚠️</Text>
          <Text style={[styles.errorText, { color: colors.text }]}>Ocorreu um erro ao carregar os itens.</Text>
          <Button title="Tentar Novamente" onPress={() => refetch()} variant="outline" style={{ marginTop: Spacing.md }} />
        </View>
      ) : !itens || itens.length === 0 ? (
        <View style={styles.centerContainer}>
          <Text style={{ fontSize: 48, marginBottom: Spacing.md }}>📦</Text>
          <Text style={[styles.emptyText, { color: colors.textSecondary }]}>Você ainda não possui itens publicados.</Text>
          <Button 
            title="Publicar um Item" 
            onPress={() => navigation.navigate('CreateItem')} 
            style={{ marginTop: Spacing.lg }} 
          />
        </View>
      ) : (
        <FlatList
          data={itens}
          keyExtractor={(item) => item.id}
          renderItem={renderItemCard}
          contentContainerStyle={styles.listContainer}
          showsVerticalScrollIndicator={false}
          onRefresh={refetch}
          refreshing={isLoading}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: Spacing.md,
    borderBottomWidth: 1,
  },
  backBtn: {
    padding: Spacing.xs,
  },
  backIcon: {
    fontSize: 24,
    fontFamily: FontFamily.bold,
  },
  title: {
    ...TextStyles.h2,
  },
  centerContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.xl,
  },
  loadingText: {
    marginTop: Spacing.sm,
    fontFamily: FontFamily.medium,
  },
  errorText: {
    fontFamily: FontFamily.medium,
    textAlign: 'center',
  },
  emptyText: {
    fontFamily: FontFamily.medium,
    textAlign: 'center',
    fontSize: FontSize.md,
  },
  listContainer: {
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
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  status: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.xs,
  },
});

export default MyItemsScreen;
