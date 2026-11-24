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
import { useStripe } from '@stripe/stripe-react-native';
import { criarLocacao, confirmarPagamento, executarAcao } from '../../api/rentals';
import { mensagemDeErro } from '../../api/auth';
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

  const { initPaymentSheet, presentPaymentSheet } = useStripe();

  // Mesmo cálculo do backend (LocacaoService): diárias = fim − início, mínimo 1
  const resumo = useMemo(() => {
    let dias = 0;
    const d1 = new Date(`${dataInicio}T00:00:00`);
    const d2 = new Date(`${dataFim}T00:00:00`);
    if (!isNaN(d1.getTime()) && !isNaN(d2.getTime()) && d2 >= d1) {
      dias = Math.max(Math.round((d2.getTime() - d1.getTime()) / 86_400_000), 1);
    }
    const subtotal = dias * precoDiaria;
    const taxaServico = Math.round(subtotal * 0.1 * 100) / 100; // 10%
    const totalAPagar = subtotal + taxaServico; // cobrado ao concluir a locação
    return { dias, subtotal, taxaServico, totalAPagar };
  }, [dataInicio, dataFim, precoDiaria]);

  const mutation = useMutation({
    mutationFn: async (): Promise<'autorizado' | 'cancelado'> => {
      if (resumo.dias <= 0) {
        throw new Error('Informe as datas no formato AAAA-MM-DD.');
      }
      // 1) Cria a locação; o backend devolve o client_secret da pré-autorização
      const locacao = await criarLocacao({ item: itemId, data_inicio: dataInicio, data_fim: dataFim });
      if (!locacao.pagamento) throw new Error('Pagamento indisponível no momento.');

      // 2) PaymentSheet do Stripe: coleta o cartão e autoriza (nada é cobrado agora)
      const init = await initPaymentSheet({
        paymentIntentClientSecret: locacao.pagamento.client_secret,
        merchantDisplayName: 'Aloogaí',
      });
      if (init.error) throw new Error(init.error.message);
      const pagamento = await presentPaymentSheet();
      if (pagamento.error) {
        // Usuário fechou a tela ou o cartão foi recusado: desfaz a solicitação
        await executarAcao(locacao.id, 'cancelar').catch(() => undefined);
        if (pagamento.error.code === 'Canceled') return 'cancelado';
        throw new Error(pagamento.error.message);
      }

      // 3) Confirma no backend (consulta o Stripe e passa para CAUCAO_RETIDA)
      await confirmarPagamento(locacao.id);
      return 'autorizado';
    },
    onSuccess: (resultado) => {
      queryClient.invalidateQueries({ queryKey: ['locacoes'] });
      if (resultado === 'cancelado') return;
      Alert.alert(
        'Pronto!',
        'Cartão autorizado. O valor só é cobrado quando a locação for concluída, e a caução é liberada na devolução.',
      );
      navigation.navigate('MainTabs');
    },
    onError: (error: unknown) => {
      const texto = error instanceof Error && !('response' in error) ? error.message : undefined;
      Alert.alert('Erro', texto ?? mensagemDeErro(error, 'Não foi possível solicitar a locação.'));
    },
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
