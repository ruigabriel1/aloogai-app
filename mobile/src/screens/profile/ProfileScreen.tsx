/**
 * ProfileScreen — Tela de perfil do Aloogaí
 *
 * Tela completa com:
 * - Avatar grande com botão de edição
 * - Nome, tipo de conta (badge P2P/B2B)
 * - Score ESG com progress circular
 * - Seção "Meus Itens"
 * - Configurações (toggle dark/light, notificações)
 * - Botão "Sair" (vermelho)
 *
 * Adapta automaticamente ao tema ativo (Light/Dark).
 */

import React, { useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme, useThemeModeStore } from '../../theme';
import { TextStyles, FontFamily, FontSize } from '../../theme/typography';
import { Spacing, BorderRadius, Shadows } from '../../theme/spacing';
import { BrandColors } from '../../theme/colors';
import { Button } from '../../components/ui/Button';
import { Avatar } from '../../components/ui/Avatar';
import { useAuthStore } from '../../store/authStore';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { MainStackParamList } from '../../navigation/types';

/** Score ESG visual circular (simplificado com View circular) */
function ScoreESGCircular({
  score,
  tamanho = 100,
}: {
  score: number;
  tamanho?: number;
}): React.JSX.Element {
  const { colors } = useTheme();
  const porcentagem = Math.min(score / 100, 1);
  const corScore =
    porcentagem > 0.7
      ? BrandColors.success
      : porcentagem > 0.4
        ? BrandColors.highlight
        : BrandColors.accent;

  return (
    <View style={[styles.esgCircular, { width: tamanho, height: tamanho }]}>
      {/* Background circle */}
      <View
        style={[
          styles.esgCircularBg,
          {
            width: tamanho,
            height: tamanho,
            borderRadius: tamanho / 2,
            borderColor: colors.border,
          },
        ]}
      />
      {/* Progress overlay (simplificado como borda colorida) */}
      <View
        style={[
          styles.esgCircularProgress,
          {
            width: tamanho,
            height: tamanho,
            borderRadius: tamanho / 2,
            borderColor: corScore,
            borderTopColor: corScore,
            borderRightColor: porcentagem > 0.25 ? corScore : colors.border,
            borderBottomColor: porcentagem > 0.5 ? corScore : colors.border,
            borderLeftColor: porcentagem > 0.75 ? corScore : colors.border,
          },
        ]}
      />
      {/* Valor central */}
      <View style={styles.esgCircularCentro}>
        <Text style={[styles.esgValor, { color: corScore }]}>
          {score.toFixed(1)}
        </Text>
        <Text style={[styles.esgLabel, { color: colors.textSecondary }]}>
          ESG
        </Text>
      </View>
    </View>
  );
}

/** Item de menu do perfil */
function MenuItem({
  icone,
  titulo,
  subtitulo,
  onPress,
  trailing,
}: {
  icone: string;
  titulo: string;
  subtitulo?: string;
  onPress?: () => void;
  trailing?: React.ReactNode;
}): React.JSX.Element {
  const { colors, isDark } = useTheme();

  return (
    <TouchableOpacity
      style={[
        styles.menuItem,
        { borderBottomColor: colors.border },
      ]}
      activeOpacity={onPress ? 0.7 : 1}
      onPress={onPress}
      disabled={!onPress && !trailing}
    >
      <View style={styles.menuItemLeft}>
        <View
          style={[
            styles.menuItemIconeContainer,
            { backgroundColor: colors.surfaceVariant },
          ]}
        >
          <Text style={styles.menuItemIcone}>{icone}</Text>
        </View>
        <View>
          <Text style={[styles.menuItemTitulo, { color: colors.text }]}>
            {titulo}
          </Text>
          {subtitulo && (
            <Text style={[styles.menuItemSubtitulo, { color: colors.textSecondary }]}>
              {subtitulo}
            </Text>
          )}
        </View>
      </View>

      {trailing || (
        onPress && (
          <Text style={[styles.menuItemSeta, { color: colors.textTertiary }]}>
            ›
          </Text>
        )
      )}
    </TouchableOpacity>
  );
}

/** Tela de Perfil */
export function ProfileScreen(): React.JSX.Element {
  const { colors, isDark, mode } = useTheme();
  const { toggle: toggleTema } = useThemeModeStore();
  const { user, logout } = useAuthStore();
  const navigation = useNavigation<NativeStackNavigationProp<MainStackParamList>>();

  /** Confirma e executa logout */
  const handleLogout = useCallback(() => {
    Alert.alert(
      'Sair da conta',
      'Tem certeza que deseja sair?',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Sair',
          style: 'destructive',
          onPress: () => logout(),
        },
      ],
    );
  }, [logout]);

  /** Placeholder para funcionalidade futura */
  const handleComingSoon = useCallback((feature: string) => {
    Alert.alert(feature, 'Esta funcionalidade estará disponível em breve!');
  }, []);

  const scoreEsg = user?.score_esg ?? 0;
  const avaliacaoMedia = user?.avaliacao_media ?? 0;

  /** Renderiza estrelas */
  const renderEstrelas = (nota: number): string => {
    const estrelas: string[] = [];
    for (let i = 1; i <= 5; i++) {
      estrelas.push(i <= Math.round(nota) ? '★' : '☆');
    }
    return estrelas.join('');
  };

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.background }]}>
      <ScrollView
        style={styles.scroll}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollConteudo}
      >
        {/* Header */}
        <Text style={[styles.headerTitulo, { color: colors.text }]}>
          Perfil
        </Text>

        {/* Card do perfil */}
        <View
          style={[
            styles.perfilCard,
            {
              backgroundColor: colors.cardBackground,
              borderColor: colors.cardBorder,
            },
            !isDark && Shadows.md,
          ]}
        >
          {/* Avatar com botão de edição */}
          <View style={styles.avatarContainer}>
            <Avatar name={user?.nome || 'Usuário'} size="xl" />
            <TouchableOpacity
              style={[
                styles.editarAvatarBotao,
                { backgroundColor: BrandColors.primary },
              ]}
              onPress={() => handleComingSoon('Editar foto')}
            >
              <Text style={styles.editarAvatarIcone}>✏️</Text>
            </TouchableOpacity>
          </View>

          {/* Nome */}
          <Text style={[styles.perfilNome, { color: colors.text }]}>
            {user?.nome || 'Usuário'}
          </Text>

          {/* Email */}
          <Text style={[styles.perfilEmail, { color: colors.textSecondary }]}>
            {user?.email || 'email@exemplo.com'}
          </Text>

          {/* Badge tipo de conta */}
          <View
            style={[
              styles.tipoBadge,
              {
                backgroundColor:
                  user?.tipo_conta === 'B2B'
                    ? BrandColors.secondary
                    : BrandColors.primary,
              },
            ]}
          >
            <Text style={styles.tipoBadgeTexto}>
              {user?.tipo_conta === 'B2B' ? '🏢 Lojista B2B' : '👤 Pessoa Física P2P'}
            </Text>
          </View>

          {/* Avaliação */}
          <View style={styles.avaliacaoRow}>
            <Text style={[styles.avaliacaoEstrelas, { color: BrandColors.highlight }]}>
              {renderEstrelas(avaliacaoMedia)}
            </Text>
            <Text style={[styles.avaliacaoNota, { color: colors.text }]}>
              {avaliacaoMedia.toFixed(1)}
            </Text>
          </View>
        </View>

        {/* Score ESG */}
        <View
          style={[
            styles.secaoCard,
            {
              backgroundColor: colors.cardBackground,
              borderColor: colors.cardBorder,
            },
            !isDark && Shadows.sm,
          ]}
        >
          <Text style={[styles.secaoTitulo, { color: colors.text }]}>
            🌱 Score ESG
          </Text>
          <View style={styles.esgConteudo}>
            <ScoreESGCircular score={scoreEsg} />
            <View style={styles.esgInfo}>
              <Text style={[styles.esgDescricao, { color: colors.textSecondary }]}>
                Seu impacto ambiental e social na comunidade.
              </Text>
              <View
                style={[
                  styles.esgDica,
                  { backgroundColor: colors.successBackground },
                ]}
              >
                <Text style={[styles.esgDicaTexto, { color: BrandColors.success }]}>
                  💡 Alugue mais e aumente seu score!
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Menu de opções */}
        <View
          style={[
            styles.secaoCard,
            {
              backgroundColor: colors.cardBackground,
              borderColor: colors.cardBorder,
            },
            !isDark && Shadows.sm,
          ]}
        >
          <MenuItem
            icone="📦"
            titulo="Meus Itens"
            subtitulo="Gerencie seus itens publicados"
            onPress={() => navigation.navigate('MyItems')}
          />
          <MenuItem
            icone="📊"
            titulo="Histórico"
            subtitulo="Todas suas locações"
            onPress={() => handleComingSoon('Histórico')}
          />
          <MenuItem
            icone="💳"
            titulo="Pagamentos"
            subtitulo="Métodos de pagamento e histórico"
            onPress={() => handleComingSoon('Pagamentos')}
          />
          <MenuItem
            icone="📄"
            titulo="Documentos"
            subtitulo="KYC e verificação de identidade"
            onPress={() => handleComingSoon('Documentos')}
          />
        </View>

        {/* Configurações */}
        <View
          style={[
            styles.secaoCard,
            {
              backgroundColor: colors.cardBackground,
              borderColor: colors.cardBorder,
            },
            !isDark && Shadows.sm,
          ]}
        >
          <Text style={[styles.secaoTitulo, { color: colors.text }]}>
            ⚙️ Configurações
          </Text>

          <MenuItem
            icone={isDark ? '🌙' : '☀️'}
            titulo="Modo Escuro"
            subtitulo={isDark ? 'Ativado' : 'Desativado'}
            trailing={
              <Switch
                value={isDark}
                onValueChange={toggleTema}
                trackColor={{
                  false: colors.border,
                  true: BrandColors.primaryLight,
                }}
                thumbColor={isDark ? BrandColors.primary : colors.surface}
              />
            }
          />
          <MenuItem
            icone="🔔"
            titulo="Notificações"
            subtitulo="Push e e-mail"
            onPress={() => handleComingSoon('Notificações')}
          />
          <MenuItem
            icone="🔒"
            titulo="Privacidade"
            subtitulo="Dados e permissões"
            onPress={() => handleComingSoon('Privacidade')}
          />
          <MenuItem
            icone="❓"
            titulo="Ajuda e Suporte"
            subtitulo="FAQ e contato"
            onPress={() => handleComingSoon('Ajuda e Suporte')}
          />
        </View>

        {/* Botão de logout */}
        <View style={styles.logoutContainer}>
          <Button
            title="Sair da conta"
            onPress={handleLogout}
            variant="outline"
            fullWidth
            size="lg"
            textStyle={{ color: BrandColors.accent }}
            style={{ borderColor: BrandColors.accent }}
            testID="botao-logout"
          />
        </View>

        {/* Versão do app */}
        <Text style={[styles.versao, { color: colors.textTertiary }]}>
          Aloogaí v0.1.0 (MVP)
        </Text>
        <Text style={[styles.slogan, { color: colors.textTertiary }]}>
          A vizinhança é seu estoque. Alugue e economize.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
  },
  scroll: {
    flex: 1,
  },
  scrollConteudo: {
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.md,
    paddingBottom: Spacing.xxl,
  },
  headerTitulo: {
    ...TextStyles.h1,
    marginBottom: Spacing.lg,
  },
  perfilCard: {
    borderRadius: BorderRadius.xl,
    borderWidth: 1,
    padding: Spacing.lg,
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  avatarContainer: {
    position: 'relative',
    marginBottom: Spacing.md,
  },
  editarAvatarBotao: {
    position: 'absolute',
    bottom: 0,
    right: -4,
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: BrandColors.white,
  },
  editarAvatarIcone: {
    fontSize: 14,
  },
  perfilNome: {
    ...TextStyles.h2,
    marginBottom: Spacing.xxs,
  },
  perfilEmail: {
    ...TextStyles.bodySmall,
    marginBottom: Spacing.md,
  },
  tipoBadge: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: BorderRadius.full,
    marginBottom: Spacing.ms,
  },
  tipoBadgeTexto: {
    fontFamily: FontFamily.semiBold,
    fontSize: FontSize.sm,
    color: BrandColors.white,
  },
  avaliacaoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  avaliacaoEstrelas: {
    fontSize: FontSize.lg,
  },
  avaliacaoNota: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.lg,
  },
  secaoCard: {
    borderRadius: BorderRadius.xl,
    borderWidth: 1,
    padding: Spacing.md,
    marginBottom: Spacing.md,
  },
  secaoTitulo: {
    ...TextStyles.h4,
    marginBottom: Spacing.md,
  },
  esgConteudo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
  },
  esgCircular: {
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  esgCircularBg: {
    position: 'absolute',
    borderWidth: 6,
  },
  esgCircularProgress: {
    position: 'absolute',
    borderWidth: 6,
  },
  esgCircularCentro: {
    alignItems: 'center',
  },
  esgValor: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.xxl,
  },
  esgLabel: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.xs,
    marginTop: -2,
  },
  esgInfo: {
    flex: 1,
  },
  esgDescricao: {
    ...TextStyles.bodySmall,
    lineHeight: 20,
    marginBottom: Spacing.sm,
  },
  esgDica: {
    paddingHorizontal: Spacing.ms,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.sm,
  },
  esgDicaTexto: {
    fontFamily: FontFamily.medium,
    fontSize: FontSize.sm,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: Spacing.ms,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.ms,
    flex: 1,
  },
  menuItemIconeContainer: {
    width: 38,
    height: 38,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuItemIcone: {
    fontSize: 18,
  },
  menuItemTitulo: {
    ...TextStyles.bodyMedium,
  },
  menuItemSubtitulo: {
    fontFamily: FontFamily.regular,
    fontSize: FontSize.xs,
    marginTop: 2,
  },
  menuItemSeta: {
    fontSize: 24,
    fontFamily: FontFamily.regular,
  },
  logoutContainer: {
    marginTop: Spacing.md,
    marginBottom: Spacing.md,
  },
  versao: {
    ...TextStyles.caption,
    textAlign: 'center',
    marginBottom: Spacing.xxs,
  },
  slogan: {
    ...TextStyles.caption,
    textAlign: 'center',
    fontStyle: 'italic',
  },
});

export default ProfileScreen;
