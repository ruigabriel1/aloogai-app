import React, { useState, useMemo } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useTheme } from '../../theme';
import { TextStyles, FontFamily } from '../../theme/typography';
import { Spacing, BorderRadius } from '../../theme/spacing';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { criarLocacao } from '../../api/rentals';
import { MainStackParamList } from '../../navigation/types';

type CheckoutRouteProp = RouteProp<MainStackParamList, 'CheckoutModal'>;
type NavigationProp = NativeStackNavigationProp<MainStackParamList>;

export function CheckoutModal(): React.JSX.Element {
  const route = useRoute<CheckoutRouteProp>();
  const navigation = useNavigation<NavigationProp>();
  const { colors } = useTheme();
  const queryClient = useQueryClient();

  const { itemId, precoDiaria, valorCaucao } = route.params;

  // No MVP simplificado usamos campos de texto para datas (YYYY-MM-DD)
  // O ideal seria integrar uma lib de calendário como react-native-calendars
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');

  // Lógica de cálculo matemático do aluguel
  const resumo = useMemo(() => {
    let dias = 0;
    try {
      const d1 = new Date(dataInicio);
      const d2 = new Date(dataFim);
      if (!isNaN(d1.getTime()) && !isNaN(d2.getTime()) && d2 >= d1) {
        const diffTime = Math.abs(d2.getTime() - d1.getTime());
        dias = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; // Pelo menos 1 diária
      }
    } catch (e) {
      // Data inválida
    }

    const subtotal = dias * precoDiaria;
    const taxaServico = subtotal * 0.10; // 10%
    const totalAPagar = subtotal + taxaServico; // Total cobrado imediatamente
    // A Caução é pré-autorizada, não cobrada imediatamente

    return { dias, subtotal, taxaServico, totalAPagar };
  }, [dataInicio, dataFim, precoDiaria]);

  const mutation = useMutation({
    mutationFn: async () => {
      if (resumo.dias <= 0) {
        throw new Error('Datas inválidas.');
      }
      return criarLocacao({
        item_id: itemId,
        data_inicio: dataInicio,
        data_fim: dataFim,
        payment_method_id: 'pm_card_br' // Mockado para Stripe test mode
      });
    },
    onSuccess: () => {
      Alert.alert('Pronto!', 'Sua solicitação de locação foi enviada ao dono do item!');
      queryClient.invalidateQueries({ queryKey: ['locacoes'] });
      navigation.navigate('MainTabs'); // Volta pro início ou vai para aba de aluguéis
    },
    onError: (error: any) => {
      Alert.alert('Erro', 'Não foi possível solicitar a locação. Verifique as datas (ex: 2026-06-10).');
    }
  });

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top', 'bottom']}>
      <View style={[styles.header, { borderBottomColor: colors.border }]}>
        <Text style={[styles.title, { color: colors.text }]}>Checkout da Locação</Text>
      </View>

      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          
          <Text style={[styles.subtitle, { color: colors.text }]}>Período do Aluguel</Text>
          
          <View style={styles.row}>
            <View style={styles.half}>
              <Input
                label="Data de Início"
                placeholder="AAAA-MM-DD"
                value={dataInicio}
                onChangeText={setDataInicio}
                keyboardType="numeric"
              />
            </View>
            <View style={styles.half}>
              <Input
                label="Data de Devolução"
                placeholder="AAAA-MM-DD"
                value={dataFim}
                onChangeText={setDataFim}
                keyboardType="numeric"
              />
            </View>
          </View>

          <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Text style={[styles.cardTitle, { color: colors.text }]}>Resumo Financeiro</Text>
            
            <View style={styles.receiptRow}>
              <Text style={{ color: colors.textSecondary }}>Diárias ({resumo.dias} dias x R$ {precoDiaria.toFixed(2)})</Text>
              <Text style={{ color: colors.text }}>R$ {resumo.subtotal.toFixed(2)}</Text>
            </View>
            
            <View style={styles.receiptRow}>
              <Text style={{ color: colors.textSecondary }}>Taxa do App (10%)</Text>
              <Text style={{ color: colors.text }}>R$ {resumo.taxaServico.toFixed(2)}</Text>
            </View>

            <View style={[styles.divider, { backgroundColor: colors.border }]} />

            <View style={styles.receiptRow}>
              <Text style={[styles.totalLabel, { color: colors.text }]}>Total a Pagar Hoje</Text>
              <Text style={[styles.totalValue, { color: colors.primary }]}>R$ {resumo.totalAPagar.toFixed(2)}</Text>
            </View>
          </View>

          <View style={[styles.alertBox, { backgroundColor: colors.surfaceVariant }]}>
            <Text style={{ fontSize: 20, marginRight: Spacing.sm }}>🔒</Text>
            <Text style={[styles.alertText, { color: colors.text }]}>
              R$ {valorCaucao.toFixed(2)} serão apenas <Text style={{ fontFamily: FontFamily.bold }}>pré-autorizados</Text> (Caução) no seu cartão de crédito e não serão cobrados se o item for devolvido sem danos.
            </Text>
          </View>

        </ScrollView>

        <View style={[styles.footer, { borderTopColor: colors.border, backgroundColor: colors.background }]}>
          <Button 
            title="Cancelar" 
            variant="ghost" 
            onPress={() => navigation.goBack()} 
            style={styles.cancelBtn} 
          />
          <Button 
            title={mutation.isPending ? "Processando..." : "Confirmar Locação"} 
            onPress={() => mutation.mutate()} 
            disabled={mutation.isPending || resumo.dias <= 0}
            style={styles.submitBtn} 
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  flex: { flex: 1 },
  header: {
    padding: Spacing.md,
    borderBottomWidth: 1,
  },
  title: { ...TextStyles.h2 },
  scrollContent: {
    padding: Spacing.md,
    gap: Spacing.md,
  },
  subtitle: {
    ...TextStyles.h3,
    marginBottom: Spacing.xs,
  },
  row: {
    flexDirection: 'row',
    gap: Spacing.md,
  },
  half: { flex: 1 },
  card: {
    borderWidth: 1,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginTop: Spacing.md,
  },
  cardTitle: {
    fontFamily: FontFamily.semiBold,
    fontSize: 16,
    marginBottom: Spacing.md,
  },
  receiptRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Spacing.sm,
  },
  divider: {
    height: 1,
    marginVertical: Spacing.sm,
  },
  totalLabel: {
    fontFamily: FontFamily.bold,
    fontSize: 16,
  },
  totalValue: {
    fontFamily: FontFamily.bold,
    fontSize: 18,
  },
  alertBox: {
    flexDirection: 'row',
    padding: Spacing.md,
    borderRadius: BorderRadius.md,
    marginTop: Spacing.xl,
    alignItems: 'center',
  },
  alertText: {
    flex: 1,
    ...TextStyles.caption,
    lineHeight: 20,
  },
  footer: {
    flexDirection: 'row',
    padding: Spacing.md,
    borderTopWidth: 1,
    gap: Spacing.md,
  },
  cancelBtn: { flex: 1 },
  submitBtn: { flex: 2 },
});

export default CheckoutModal;
