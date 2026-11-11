/**
 * MessageBubble — Bolha de mensagem do chat Aloogaí
 *
 * Componente de bolha com:
 * - Alinhamento: direita (enviada) vs esquerda (recebida)
 * - Cor: verde (enviada) vs cinza (recebida)
 * - Timestamp e status de leitura (✓✓)
 *
 * Adapta automaticamente ao tema ativo (Light/Dark).
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '../../theme';
import { FontFamily, FontSize } from '../../theme/typography';
import { Spacing, BorderRadius } from '../../theme/spacing';
import { BrandColors } from '../../theme/colors';

/** Props do MessageBubble */
export interface MessageBubbleProps {
  /** Conteúdo textual da mensagem */
  conteudo: string;
  /** Se a mensagem foi enviada pelo usuário atual */
  enviada: boolean;
  /** Se a mensagem foi lida pelo destinatário */
  lida?: boolean;
  /** Timestamp ISO da mensagem */
  timestamp: string;
  /** Nome do remetente (exibido em recebidas) */
  nomeRemetente?: string;
}

/** Formata timestamp ISO para HH:MM */
function formatarHora(iso: string): string {
  const data = new Date(iso);
  const horas = data.getHours().toString().padStart(2, '0');
  const minutos = data.getMinutes().toString().padStart(2, '0');
  return `${horas}:${minutos}`;
}

/** Bolha de mensagem para o chat */
export function MessageBubble({
  conteudo,
  enviada,
  lida = false,
  timestamp,
  nomeRemetente,
}: MessageBubbleProps): React.JSX.Element {
  const { colors, isDark } = useTheme();

  // Cores da bolha
  const bgBolha = enviada
    ? BrandColors.primary
    : isDark
      ? colors.surfaceVariant
      : colors.surface;

  const textColor = enviada
    ? BrandColors.white
    : colors.text;

  const metaColor = enviada
    ? 'rgba(255, 255, 255, 0.7)'
    : colors.textTertiary;

  return (
    <View
      style={[
        styles.container,
        enviada ? styles.containerEnviada : styles.containerRecebida,
      ]}
    >
      <View
        style={[
          styles.bolha,
          enviada ? styles.bolhaEnviada : styles.bolhaRecebida,
          { backgroundColor: bgBolha },
        ]}
      >
        {/* Nome do remetente (somente recebidas) */}
        {!enviada && nomeRemetente && (
          <Text style={[styles.nomeRemetente, { color: BrandColors.primary }]}>
            {nomeRemetente}
          </Text>
        )}

        {/* Conteúdo da mensagem */}
        <Text style={[styles.conteudo, { color: textColor }]}>
          {conteudo}
        </Text>

        {/* Footer: timestamp + status de leitura */}
        <View style={styles.footer}>
          <Text style={[styles.timestamp, { color: metaColor }]}>
            {formatarHora(timestamp)}
          </Text>
          {enviada && (
            <Text style={[styles.statusLeitura, { color: metaColor }]}>
              {lida ? '✓✓' : '✓'}
            </Text>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: Spacing.xxs,
    marginHorizontal: Spacing.md,
  },
  containerEnviada: {
    alignItems: 'flex-end',
  },
  containerRecebida: {
    alignItems: 'flex-start',
  },
  bolha: {
    maxWidth: '80%',
    paddingHorizontal: Spacing.ms,
    paddingTop: Spacing.sm,
    paddingBottom: Spacing.xs,
  },
  bolhaEnviada: {
    borderTopLeftRadius: BorderRadius.lg,
    borderTopRightRadius: BorderRadius.lg,
    borderBottomLeftRadius: BorderRadius.lg,
    borderBottomRightRadius: BorderRadius.xs,
  },
  bolhaRecebida: {
    borderTopLeftRadius: BorderRadius.xs,
    borderTopRightRadius: BorderRadius.lg,
    borderBottomLeftRadius: BorderRadius.lg,
    borderBottomRightRadius: BorderRadius.lg,
  },
  nomeRemetente: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.xs,
    marginBottom: 2,
  },
  conteudo: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.base,
    lineHeight: 22,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginTop: 2,
    gap: 4,
  },
  timestamp: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.xs,
  },
  statusLeitura: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.xs,
  },
});

export default MessageBubble;
