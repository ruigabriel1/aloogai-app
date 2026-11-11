import React from 'react';
import { View, Text, StyleSheet, ScrollView, Image, ActivityIndicator, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from '../../theme';
import { TextStyles, FontFamily } from '../../theme/typography';
import { Spacing, BorderRadius } from '../../theme/spacing';
import { Button } from '../../components/ui/Button';
import { buscarItemDetalhe } from '../../api/catalog';
import { MainStackParamList } from '../../navigation/types';
import { useAuthStore } from '../../store/authStore';

type ItemDetailRouteProp = RouteProp<MainStackParamList, 'ItemDetalhe'>;
type NavigationProp = NativeStackNavigationProp<MainStackParamList>;

export function ItemDetailScreen(): React.JSX.Element {
  const route = useRoute<ItemDetailRouteProp>();
  const navigation = useNavigation<NavigationProp>();
  const { colors } = useTheme();
  const { user } = useAuthStore();
  const { itemId } = route.params;

  const { data: item, isLoading, isError } = useQuery({
    queryKey: ['item-detalhe', itemId],
    queryFn: () => buscarItemDetalhe(itemId),
  });

  if (isLoading) {
    return (
      <View style={[styles.center, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (isError || !item) {
    return (
      <View style={[styles.center, { backgroundColor: colors.background }]}>
        <Text style={[styles.errorText, { color: colors.error }]}>Erro ao carregar os detalhes do item.</Text>
        <Button title="Voltar" onPress={() => navigation.goBack()} style={{ marginTop: Spacing.md }} />
      </View>
    );
  }

  const handleAlugar = () => {
    if (user?.id === item.locador.id) {
      Alert.alert('Ops', 'Você não pode alugar o seu próprio item!');
      return;
    }
    navigation.navigate('CheckoutModal', {
      itemId: item.id,
      precoDiaria: parseFloat(item.preco_diaria),
      valorCaucao: parseFloat(item.valor_caucao),
    });
  };

  const fotoCapa = item.fotos?.find(f => f.is_capa) || item.fotos?.[0];
  const urlCapa = fotoCapa?.url || 'https://via.placeholder.com/400x300.png?text=Sem+Foto';

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Image source={{ uri: urlCapa }} style={styles.image} />

        <View style={styles.content}>
          <Text style={[styles.title, { color: colors.text }]}>{item.titulo}</Text>
          
          <View style={styles.row}>
            <Text style={[styles.price, { color: colors.primary }]}>R$ {item.preco_diaria} / dia</Text>
            <View style={[styles.badge, { backgroundColor: colors.surfaceVariant }]}>
              <Text style={[styles.badgeText, { color: colors.text }]}>★ {item.avaliacao_media.toFixed(1)}</Text>
            </View>
          </View>

          <View style={[styles.divider, { backgroundColor: colors.border }]} />

          <Text style={[styles.sectionTitle, { color: colors.text }]}>Sobre o item</Text>
          <Text style={[styles.description, { color: colors.textSecondary }]}>{item.descricao}</Text>

          <View style={[styles.divider, { backgroundColor: colors.border }]} />

          <Text style={[styles.sectionTitle, { color: colors.text }]}>Locador</Text>
          <View style={styles.locadorRow}>
            <View style={[styles.avatar, { backgroundColor: colors.surfaceVariant }]}>
              <Text style={{ fontSize: 24 }}>👤</Text>
            </View>
            <View style={styles.locadorInfo}>
              <Text style={[styles.locadorName, { color: colors.text }]}>{item.locador.nome}</Text>
              <Text style={[styles.esgScore, { color: colors.success }]}>🌱 ESG Score: {item.locador.score_esg}</Text>
            </View>
          </View>

          <View style={[styles.infoBox, { backgroundColor: colors.surfaceVariant }]}>
            <Text style={[styles.infoTitle, { color: colors.text }]}>Caução (Pré-autorização)</Text>
            <Text style={[styles.infoText, { color: colors.textSecondary }]}>
              R$ {item.valor_caucao} será retido temporariamente no seu cartão até a devolução do item em segurança.
            </Text>
          </View>
        </View>
      </ScrollView>

      <View style={[styles.footer, { borderTopColor: colors.border, backgroundColor: colors.background }]}>
        <Button 
          title="Alugar Agora" 
          onPress={handleAlugar} 
          style={styles.rentBtn} 
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  errorText: { ...TextStyles.body, textAlign: 'center' },
  scrollContent: { paddingBottom: Spacing.xl },
  image: {
    width: '100%',
    height: 250,
    resizeMode: 'cover',
  },
  content: {
    padding: Spacing.lg,
  },
  title: {
    ...TextStyles.h2,
    marginBottom: Spacing.sm,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  price: {
    ...TextStyles.h2,
  },
  badge: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
  },
  badgeText: {
    fontFamily: FontFamily.bold,
    fontSize: 14,
  },
  divider: {
    height: 1,
    width: '100%',
    marginVertical: Spacing.lg,
  },
  sectionTitle: {
    ...TextStyles.h3,
    marginBottom: Spacing.sm,
  },
  description: {
    ...TextStyles.body,
    lineHeight: 24,
  },
  locadorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
  },
  locadorInfo: {
    flex: 1,
  },
  locadorName: {
    fontFamily: FontFamily.semiBold,
    fontSize: 16,
    marginBottom: 4,
  },
  esgScore: {
    fontFamily: FontFamily.medium,
    fontSize: 14,
  },
  infoBox: {
    marginTop: Spacing.xl,
    padding: Spacing.md,
    borderRadius: BorderRadius.md,
  },
  infoTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: 14,
    marginBottom: 4,
  },
  infoText: {
    ...TextStyles.caption,
    lineHeight: 20,
  },
  footer: {
    padding: Spacing.md,
    borderTopWidth: 1,
  },
  rentBtn: {
    width: '100%',
  },
});

export default ItemDetailScreen;
