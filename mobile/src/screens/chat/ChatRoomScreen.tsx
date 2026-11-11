/**
 * ChatRoomScreen — Tela de mensagens do Aloogaí
 *
 * Chat em tempo real com WebSocket:
 * - FlatList invertida com bolhas de mensagem
 * - Input de texto com botão enviar
 * - Indicador "Digitando..."
 * - Header com nome e item da locação
 * - Combina mensagens históricas (API) + tempo real (WS)
 *
 * Adapta automaticamente ao tema ativo (Light/Dark).
 */

import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useNavigation, useRoute, type RouteProp } from '@react-navigation/native';
import { useTheme } from '../../theme';
import { TextStyles, FontFamily, FontSize } from '../../theme/typography';
import { Spacing, BorderRadius, Shadows } from '../../theme/spacing';
import { BrandColors } from '../../theme/colors';
import { listarMensagens, type Mensagem } from '../../api/chat';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useAuthStore } from '../../store/authStore';
import { MessageBubble } from '../../components/chat/MessageBubble';
import { TypingIndicator } from '../../components/chat/TypingIndicator';
import type { MainStackParamList } from '../../navigation/types';

/** Tela de chat com mensagens */
export function ChatRoomScreen(): React.JSX.Element {
  const { colors, isDark } = useTheme();
  const navigation = useNavigation();
  const route = useRoute<RouteProp<MainStackParamList, 'ChatRoom'>>();
  const userId = useAuthStore((state) => state.user?.id);
  const flatListRef = useRef<FlatList<Mensagem>>(null);

  const { salaId, locacaoId, nomeOutroUsuario, itemTitulo } = route.params;

  // Estado do input
  const [textoMensagem, setTextoMensagem] = useState('');
  const [digitandoTimeout, setDigitandoTimeout] = useState<ReturnType<typeof setTimeout> | null>(null);

  // Mensagens históricas via API
  const {
    data: mensagensHistoricas,
    isLoading,
  } = useQuery({
    queryKey: ['mensagens', salaId],
    queryFn: () => listarMensagens(salaId),
  });

  // WebSocket para tempo real
  const {
    conectado,
    mensagens: mensagensWS,
    digitando,
    enviarMensagem: enviarMensagemWS,
    enviarDigitando,
  } = useWebSocket(locacaoId);

  // Combina mensagens históricas + tempo real (sem duplicatas)
  const todasMensagens = useMemo(() => {
    const historicas = mensagensHistoricas || [];
    const idsHistoricos = new Set(historicas.map((m) => m.id));

    // Adiciona apenas mensagens WS que não estão no histórico
    const novasMensagensWS = mensagensWS.filter(
      (m) => !idsHistoricos.has(m.id),
    );

    // Invertida: mais recentes primeiro (para FlatList invertida)
    return [...historicas, ...novasMensagensWS].sort(
      (a, b) => new Date(b.criado_em).getTime() - new Date(a.criado_em).getTime(),
    );
  }, [mensagensHistoricas, mensagensWS]);

  /** Envia a mensagem */
  const handleEnviar = useCallback(() => {
    const texto = textoMensagem.trim();
    if (!texto) return;

    enviarMensagemWS(texto);
    setTextoMensagem('');
  }, [textoMensagem, enviarMensagemWS]);

  /** Notifica que está digitando (debounced) */
  const handleTextoChange = useCallback(
    (texto: string) => {
      setTextoMensagem(texto);

      // Debounce do evento de digitação
      if (digitandoTimeout) {
        clearTimeout(digitandoTimeout);
      }

      if (texto.length > 0) {
        enviarDigitando();
        setDigitandoTimeout(
          setTimeout(() => {
            // Sem ação após 3s sem digitar
          }, 3000),
        );
      }
    },
    [enviarDigitando, digitandoTimeout],
  );

  /** Renderiza uma mensagem */
  const renderMensagem = ({ item: mensagem }: { item: Mensagem }) => {
    const enviada = mensagem.remetente.id === userId;

    return (
      <MessageBubble
        conteudo={mensagem.conteudo}
        enviada={enviada}
        lida={mensagem.lida}
        timestamp={mensagem.criado_em}
        nomeRemetente={!enviada ? mensagem.remetente.nome : undefined}
      />
    );
  };

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View
        style={[
          styles.header,
          {
            backgroundColor: colors.cardBackground,
            borderBottomColor: colors.border,
          },
          !isDark && Shadows.sm,
        ]}
      >
        <TouchableOpacity
          style={styles.botaoVoltar}
          onPress={() => navigation.goBack()}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Text style={[styles.botaoVoltarTexto, { color: colors.text }]}>
            ←
          </Text>
        </TouchableOpacity>

        <View style={styles.headerInfo}>
          <View style={styles.headerNomeRow}>
            <Text
              style={[styles.headerNome, { color: colors.text }]}
              numberOfLines={1}
            >
              {nomeOutroUsuario}
            </Text>
            {/* Indicador de conexão */}
            <View
              style={[
                styles.statusDot,
                {
                  backgroundColor: conectado
                    ? BrandColors.success
                    : colors.textTertiary,
                },
              ]}
            />
          </View>
          <Text
            style={[styles.headerItem, { color: colors.textSecondary }]}
            numberOfLines={1}
          >
            📦 {itemTitulo}
          </Text>
        </View>
      </View>

      {/* Conteúdo do chat */}
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={0}
      >
        {/* Mensagens */}
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={BrandColors.primary} />
            <Text style={[styles.loadingTexto, { color: colors.textSecondary }]}>
              Carregando mensagens...
            </Text>
          </View>
        ) : (
          <FlatList
            ref={flatListRef}
            data={todasMensagens}
            renderItem={renderMensagem}
            keyExtractor={(item) => item.id}
            inverted
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.mensagensConteudo}
            ListHeaderComponent={
              digitando ? (
                <TypingIndicator
                  nome={digitando.nome}
                  visivel={true}
                />
              ) : null
            }
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyIcone}>💬</Text>
                <Text style={[styles.emptyTexto, { color: colors.textSecondary }]}>
                  Nenhuma mensagem ainda.{'\n'}Diga olá!
                </Text>
              </View>
            }
          />
        )}

        {/* Input de mensagem */}
        <View
          style={[
            styles.inputContainer,
            {
              backgroundColor: colors.cardBackground,
              borderTopColor: colors.border,
            },
          ]}
        >
          <TextInput
            style={[
              styles.input,
              {
                backgroundColor: colors.inputBackground,
                borderColor: colors.inputBorder,
                color: colors.text,
              },
            ]}
            placeholder="Digite uma mensagem..."
            placeholderTextColor={colors.inputPlaceholder}
            value={textoMensagem}
            onChangeText={handleTextoChange}
            multiline
            maxLength={1000}
            returnKeyType="default"
          />
          <TouchableOpacity
            style={[
              styles.botaoEnviar,
              {
                backgroundColor: textoMensagem.trim()
                  ? BrandColors.primary
                  : colors.surfaceVariant,
              },
            ]}
            onPress={handleEnviar}
            disabled={!textoMensagem.trim()}
            activeOpacity={0.7}
          >
            <Text
              style={[
                styles.botaoEnviarTexto,
                {
                  color: textoMensagem.trim()
                    ? BrandColors.white
                    : colors.textTertiary,
                },
              ]}
            >
              ➤
            </Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
  },
  flex: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.ms,
    borderBottomWidth: 1,
    gap: Spacing.ms,
  },
  botaoVoltar: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  botaoVoltarTexto: {
    fontSize: 24,
  },
  headerInfo: {
    flex: 1,
  },
  headerNomeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  headerNome: {
    ...TextStyles.bodyBold,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  headerItem: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.sm,
    marginTop: 2,
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
  mensagensConteudo: {
    paddingVertical: Spacing.sm,
    flexGrow: 1,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.huge,
    transform: [{ scaleY: -1 }], // Inverte pois FlatList é invertida
  },
  emptyIcone: {
    fontSize: 48,
    marginBottom: Spacing.md,
  },
  emptyTexto: {
    ...TextStyles.body,
    textAlign: 'center',
    lineHeight: 22,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderTopWidth: 1,
    gap: Spacing.sm,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderRadius: BorderRadius.xl,
    paddingHorizontal: Spacing.md,
    paddingVertical: Platform.OS === 'ios' ? Spacing.ms : Spacing.sm,
    fontFamily: FontFamily.regular,
    fontSize: FontSize.base,
    maxHeight: 100,
  },
  botaoEnviar: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
  },
  botaoEnviarTexto: {
    fontSize: 20,
  },
});

export default ChatRoomScreen;
