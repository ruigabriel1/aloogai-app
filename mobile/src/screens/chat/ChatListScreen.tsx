/**
 * ChatListScreen — Lista de conversas do Aloogaí
 *
 * Exibe todas as salas de chat do usuário:
 * - Avatar do outro participante
 * - Última mensagem e timestamp
 * - Badge de mensagens não lidas
 * - Pull to refresh
 * - Empty state bonito
 *
 * Adapta automaticamente ao tema ativo (Light/Dark).
 */

import React, { useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useTheme } from '../../theme';
import { TextStyles, FontFamily, FontSize } from '../../theme/typography';
import { Spacing, BorderRadius, Shadows } from '../../theme/spacing';
import { BrandColors } from '../../theme/colors';
import { listarSalas, type SalaChat } from '../../api/chat';
import { useAuthStore } from '../../store/authStore';
import type { MainStackParamList } from '../../navigation/types';

/** Formata timestamp para exibição relativa */
function formatarTempo(iso: string): string {
  const agora = new Date();
  const data = new Date(iso);
  const diffMs = agora.getTime() - data.getTime();
  const diffMin = Math.floor(diffMs / (1000 * 60));
  const diffHoras = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDias = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMin < 1) return 'Agora';
  if (diffMin < 60) return `${diffMin}min`;
  if (diffHoras < 24) return `${diffHoras}h`;
  if (diffDias < 7) return `${diffDias}d`;

  const dia = data.getDate().toString().padStart(2, '0');
  const mes = (data.getMonth() + 1).toString().padStart(2, '0');
  return `${dia}/${mes}`;
}

/** Tela de lista de chats */
export function ChatListScreen(): React.JSX.Element {
  const { colors, isDark } = useTheme();
  const navigation = useNavigation<NativeStackNavigationProp<MainStackParamList>>();
  const userId = useAuthStore((state) => state.user?.id);

  // Query de salas
  const {
    data: salas,
    isLoading,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['salas-chat'],
    queryFn: listarSalas,
  });

  /** Navega para a sala de chat */
  const irParaSala = useCallback(
    (sala: SalaChat) => {
      navigation.navigate('ChatRoom', {
        salaId: sala.id,
        locacaoId: sala.locacao_id,
        nomeOutroUsuario: getOutroParticipante(sala)?.nome || 'Chat',
        itemTitulo: sala.item.titulo,
      });
    },
    [navigation, userId],
  );

  /** Obtém o outro participante da sala */
  const getOutroParticipante = useCallback(
    (sala: SalaChat) => {
      return sala.participantes.find((p) => p.id !== userId) || sala.participantes[0];
    },
    [userId],
  );

  /** Renderiza uma sala de chat */
  const renderSala = ({ item: sala }: { item: SalaChat }) => {
    const outroUsuario = getOutroParticipante(sala);
    const temNaoLidas = sala.nao_lidas > 0;

    return (
      <TouchableOpacity
        style={[
          styles.salaCard,
          {
            backgroundColor: temNaoLidas
              ? isDark
                ? colors.surfaceVariant
                : '#F0FFF0'
              : colors.cardBackground,
            borderColor: colors.cardBorder,
          },
        ]}
        activeOpacity={0.7}
        onPress={() => irParaSala(sala)}
      >
        {/* Avatar */}
        <View
          style={[
            styles.avatar,
            { backgroundColor: BrandColors.primary },
          ]}
        >
          <Text style={styles.avatarTexto}>
            {outroUsuario?.nome.charAt(0).toUpperCase() || '?'}
          </Text>
        </View>

        {/* Informações */}
        <View style={styles.salaInfo}>
          <View style={styles.salaHeader}>
            <Text
              style={[
                styles.salaNome,
                { color: colors.text },
                temNaoLidas && styles.salaNomeBold,
              ]}
              numberOfLines={1}
            >
              {outroUsuario?.nome || 'Usuário'}
            </Text>
            {sala.ultima_mensagem && (
              <Text style={[styles.salaTempo, { color: colors.textTertiary }]}>
                {formatarTempo(sala.ultima_mensagem.criado_em)}
              </Text>
            )}
          </View>

          <View style={styles.salaSubheader}>
            <Text
              style={[
                styles.salaItemTitulo,
                { color: colors.textTertiary },
              ]}
              numberOfLines={1}
            >
              📦 {sala.item.titulo}
            </Text>
          </View>

          <View style={styles.salaRodape}>
            <Text
              style={[
                styles.salaUltimaMensagem,
                { color: colors.textSecondary },
                temNaoLidas && styles.salaUltimaMensagemBold,
              ]}
              numberOfLines={1}
            >
              {sala.ultima_mensagem?.conteudo || 'Nenhuma mensagem ainda'}
            </Text>

            {/* Badge de não lidas */}
            {temNaoLidas && (
              <View style={styles.naoLidasBadge}>
                <Text style={styles.naoLidasTexto}>
                  {sala.nao_lidas > 99 ? '99+' : sala.nao_lidas}
                </Text>
              </View>
            )}
          </View>
        </View>
      </TouchableOpacity>
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
        <Text style={styles.emptyIcone}>💬</Text>
      </View>
      <Text style={[styles.emptyTitulo, { color: colors.text }]}>
        Nenhuma conversa ainda
      </Text>
      <Text style={[styles.emptySubtitulo, { color: colors.textSecondary }]}>
        Suas conversas com locadores{'\n'}aparecerão aqui após solicitar{'\n'}uma locação.
      </Text>
    </View>
  );

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.headerTitulo, { color: colors.text }]}>
          Conversas
        </Text>
      </View>

      {/* Lista de salas */}
      {isLoading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={BrandColors.primary} />
          <Text style={[styles.loadingTexto, { color: colors.textSecondary }]}>
            Carregando conversas...
          </Text>
        </View>
      ) : (
        <FlatList
          data={salas || []}
          renderItem={renderSala}
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
          ItemSeparatorComponent={() => (
            <View style={[styles.separador, { backgroundColor: colors.border }]} />
          )}
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
    flexGrow: 1,
  },
  salaCard: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.ms,
    gap: Spacing.ms,
    alignItems: 'center',
  },
  avatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarTexto: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.xl,
    color: BrandColors.white,
  },
  salaInfo: {
    flex: 1,
  },
  salaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 2,
  },
  salaNome: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.base,
    flex: 1,
  },
  salaNomeBold: {
    fontFamily: FontFamily.bold,
  },
  salaTempo: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.xs,
    marginLeft: Spacing.sm,
  },
  salaSubheader: {
    marginBottom: 4,
  },
  salaItemTitulo: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.xs,
  },
  salaRodape: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  salaUltimaMensagem: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.sm,
    flex: 1,
  },
  salaUltimaMensagemBold: {
    fontFamily: FontFamily.semiBold,
  },
  naoLidasBadge: {
    backgroundColor: BrandColors.primary,
    minWidth: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 6,
    marginLeft: Spacing.sm,
  },
  naoLidasTexto: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.xs,
    color: BrandColors.white,
  },
  separador: {
    height: 1,
    marginLeft: 76, // Alinhado após o avatar
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

export default ChatListScreen;
