/**
 * LoginScreen — Tela de login do Aloogaí
 *
 * Design premium com logo, slogan, campos de email/senha
 * e navegação para registro. Adaptada a Light/Dark mode.
 */

import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  Image,
  TextInput,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  Alert,
} from 'react-native';
import { type NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { AuthStackParamList } from '../../navigation/types';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useTheme } from '../../theme';
import { TextStyles, FontFamily, FontSize } from '../../theme/typography';
import { Spacing, BorderRadius, Shadows } from '../../theme/spacing';
import { BrandColors } from '../../theme/colors';
import { authApi } from '../../api/auth';
import { useAuthStore } from '../../store/authStore';

type LoginNavProp = NativeStackNavigationProp<AuthStackParamList, 'Login'>;

const { width: SCREEN_WIDTH } = Dimensions.get('window');

/** Tela de login com design premium */
export function LoginScreen(): React.JSX.Element {
  const navigation = useNavigation<LoginNavProp>();
  const { colors, isDark } = useTheme();
  const { login: authLogin } = useAuthStore();

  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; senha?: string }>({});

  const senhaRef = useRef<TextInput>(null);

  /** Validação dos campos */
  const validar = (): boolean => {
    const novoErrors: { email?: string; senha?: string } = {};

    if (!email.trim()) {
      novoErrors.email = 'E-mail é obrigatório';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      novoErrors.email = 'E-mail inválido';
    }

    if (!senha.trim()) {
      novoErrors.senha = 'Senha é obrigatória';
    } else if (senha.length < 6) {
      novoErrors.senha = 'Mínimo de 6 caracteres';
    }

    setErrors(novoErrors);
    return Object.keys(novoErrors).length === 0;
  };

  /** Faz login na API */
  const handleLogin = async () => {
    if (!validar()) return;

    setLoading(true);
    try {
      const response = await authApi.login({
        email: email.trim().toLowerCase(),
        password: senha,
      });
      await authLogin(response.access, response.refresh, response.user);
    } catch (error: unknown) {
      const mensagem =
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'E-mail ou senha incorretos. Tente novamente.';
      Alert.alert('Erro no login', mensagem);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.background }]}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.flex}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Header com logo e slogan */}
          <View style={styles.headerContainer}>
            {/* Fundo decorativo verde */}
            <View
              style={[
                styles.headerDecoration,
                { backgroundColor: isDark ? BrandColors.primaryDark : BrandColors.primary },
              ]}
            />

            {/* Logo */}
            <View style={[styles.logoContainer, { backgroundColor: colors.background }]}>
              <Image
                source={require('../../../assets/logo.jpeg')}
                style={styles.logo}
                resizeMode="contain"
              />
            </View>

            {/* Nome e slogan */}
            <Text style={[styles.appName, { color: BrandColors.primary }]}>
              Aloogaí
            </Text>
            <Text style={[styles.slogan, { color: colors.textSecondary }]}>
              A vizinhança é seu estoque.{'\n'}Alugue e economize.
            </Text>
          </View>

          {/* Formulário de login */}
          <View
            style={[
              styles.formContainer,
              {
                backgroundColor: colors.cardBackground,
                borderColor: colors.cardBorder,
              },
              !isDark && Shadows.md,
            ]}
          >
            <Text style={[styles.formTitle, { color: colors.text }]}>
              Bem-vindo de volta!
            </Text>
            <Text style={[styles.formSubtitle, { color: colors.textSecondary }]}>
              Entre na sua conta para continuar
            </Text>

            {/* Campo de e-mail */}
            <Input
              label="E-mail"
              placeholder="seu@email.com"
              value={email}
              onChangeText={(text) => {
                setEmail(text);
                if (errors.email) setErrors((prev) => ({ ...prev, email: undefined }));
              }}
              error={errors.email}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              returnKeyType="next"
              onSubmitEditing={() => senhaRef.current?.focus()}
              leftIcon={
                <Text style={{ fontSize: 18, opacity: 0.6 }}>📧</Text>
              }
              testID="input-email"
            />

            {/* Campo de senha */}
            <Input
              ref={senhaRef}
              label="Senha"
              placeholder="Sua senha"
              value={senha}
              onChangeText={(text) => {
                setSenha(text);
                if (errors.senha) setErrors((prev) => ({ ...prev, senha: undefined }));
              }}
              error={errors.senha}
              secureTextEntry={!mostrarSenha}
              autoCapitalize="none"
              returnKeyType="done"
              onSubmitEditing={handleLogin}
              leftIcon={
                <Text style={{ fontSize: 18, opacity: 0.6 }}>🔒</Text>
              }
              rightIcon={
                <Text style={{ fontSize: 18, opacity: 0.6 }}>
                  {mostrarSenha ? '👁️' : '🙈'}
                </Text>
              }
              onRightIconPress={() => setMostrarSenha(!mostrarSenha)}
              testID="input-senha"
            />

            {/* Link de esqueceu senha */}
            <TouchableOpacity style={styles.forgotPassword}>
              <Text style={[styles.forgotPasswordText, { color: BrandColors.primary }]}>
                Esqueceu sua senha?
              </Text>
            </TouchableOpacity>

            {/* Botão de login */}
            <Button
              title="Entrar"
              onPress={handleLogin}
              loading={loading}
              disabled={loading}
              fullWidth
              size="lg"
              testID="botao-entrar"
            />
          </View>

          {/* Link para registro */}
          <View style={styles.registerContainer}>
            <Text style={[styles.registerText, { color: colors.textSecondary }]}>
              Ainda não tem conta?{' '}
            </Text>
            <TouchableOpacity onPress={() => navigation.navigate('Register')}>
              <Text style={[styles.registerLink, { color: BrandColors.primary }]}>
                Criar conta
              </Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
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
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: Spacing.lg,
    paddingBottom: Spacing.xl,
  },
  headerContainer: {
    alignItems: 'center',
    marginTop: Spacing.xl,
    marginBottom: Spacing.lg,
    position: 'relative',
  },
  headerDecoration: {
    position: 'absolute',
    top: -100,
    left: -SCREEN_WIDTH,
    right: -SCREEN_WIDTH,
    height: 200,
    borderBottomLeftRadius: 999,
    borderBottomRightRadius: 999,
    opacity: 0.08,
  },
  logoContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    overflow: 'hidden',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 6,
  },
  logo: {
    width: 100,
    height: 100,
  },
  appName: {
    fontFamily: FontFamily.bold,
    fontSize: FontSize.display,
    marginBottom: Spacing.xs,
  },
  slogan: {
    ...TextStyles.bodySmall,
    textAlign: 'center',
    lineHeight: 20,
  },
  formContainer: {
    borderRadius: BorderRadius.xl,
    borderWidth: 1,
    padding: Spacing.lg,
    marginBottom: Spacing.lg,
  },
  formTitle: {
    ...TextStyles.h3,
    marginBottom: Spacing.xs,
  },
  formSubtitle: {
    ...TextStyles.bodySmall,
    marginBottom: Spacing.lg,
  },
  forgotPassword: {
    alignSelf: 'flex-end',
    marginBottom: Spacing.lg,
    marginTop: -Spacing.sm,
  },
  forgotPasswordText: {
    ...TextStyles.labelSmall,
  },
  registerContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: Spacing.sm,
  },
  registerText: {
    ...TextStyles.body,
  },
  registerLink: {
    ...TextStyles.bodyBold,
  },
});

export default LoginScreen;
