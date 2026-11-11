/**
 * RegisterScreen — Tela de registro do Aloogaí
 *
 * Formulário completo com nome, email, CPF, telefone, senha.
 * Seletor P2P/B2B, validação em tempo real, design premium.
 * Adaptada a Light/Dark mode.
 */

import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  TouchableOpacity,
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

type RegisterNavProp = NativeStackNavigationProp<AuthStackParamList, 'Register'>;

/** Tipo de conta selecionável */
type TipoConta = 'P2P' | 'B2B';

/**
 * Aplica máscara de CPF: 000.000.000-00
 */
function mascaraCPF(value: string): string {
  const nums = value.replace(/\D/g, '').slice(0, 11);
  return nums
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
}

/**
 * Aplica máscara de telefone: (00) 00000-0000
 */
function mascaraTelefone(value: string): string {
  const nums = value.replace(/\D/g, '').slice(0, 11);
  return nums
    .replace(/(\d{2})(\d)/, '($1) $2')
    .replace(/(\d{5})(\d{1,4})$/, '$1-$2');
}

/**
 * Validação simples de CPF (verifica dígitos verificadores).
 */
function validarCPF(cpf: string): boolean {
  const nums = cpf.replace(/\D/g, '');
  if (nums.length !== 11) return false;
  if (/^(\d)\1+$/.test(nums)) return false;

  let soma = 0;
  for (let i = 0; i < 9; i++) {
    soma += parseInt(nums[i]) * (10 - i);
  }
  let resto = (soma * 10) % 11;
  if (resto === 10) resto = 0;
  if (resto !== parseInt(nums[9])) return false;

  soma = 0;
  for (let i = 0; i < 10; i++) {
    soma += parseInt(nums[i]) * (11 - i);
  }
  resto = (soma * 10) % 11;
  if (resto === 10) resto = 0;
  return resto === parseInt(nums[10]);
}

/** Tela de registro com validação completa */
export function RegisterScreen(): React.JSX.Element {
  const navigation = useNavigation<RegisterNavProp>();
  const { colors, isDark } = useTheme();
  const { login: authLogin } = useAuthStore();

  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [cpf, setCpf] = useState('');
  const [telefone, setTelefone] = useState('');
  const [senha, setSenha] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');
  const [tipoConta, setTipoConta] = useState<TipoConta>('P2P');
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const emailRef = useRef<TextInput>(null);
  const cpfRef = useRef<TextInput>(null);
  const telefoneRef = useRef<TextInput>(null);
  const senhaRef = useRef<TextInput>(null);
  const confirmarSenhaRef = useRef<TextInput>(null);

  /** Validação completa dos campos */
  const validar = (): boolean => {
    const novoErrors: Record<string, string> = {};

    if (!nome.trim() || nome.trim().length < 3) {
      novoErrors.nome = 'Nome deve ter pelo menos 3 caracteres';
    }

    if (!email.trim()) {
      novoErrors.email = 'E-mail é obrigatório';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      novoErrors.email = 'E-mail inválido';
    }

    const cpfLimpo = cpf.replace(/\D/g, '');
    if (!cpfLimpo) {
      novoErrors.cpf = 'CPF é obrigatório';
    } else if (!validarCPF(cpfLimpo)) {
      novoErrors.cpf = 'CPF inválido';
    }

    const telLimpo = telefone.replace(/\D/g, '');
    if (!telLimpo) {
      novoErrors.telefone = 'Telefone é obrigatório';
    } else if (telLimpo.length < 10) {
      novoErrors.telefone = 'Telefone inválido';
    }

    if (!senha) {
      novoErrors.senha = 'Senha é obrigatória';
    } else if (senha.length < 8) {
      novoErrors.senha = 'Mínimo de 8 caracteres';
    } else if (!/(?=.*[A-Z])(?=.*\d)/.test(senha)) {
      novoErrors.senha = 'Deve conter letra maiúscula e número';
    }

    if (senha !== confirmarSenha) {
      novoErrors.confirmarSenha = 'As senhas não coincidem';
    }

    setErrors(novoErrors);
    return Object.keys(novoErrors).length === 0;
  };

  /** Envia registro para a API */
  const handleRegister = async () => {
    if (!validar()) return;

    setLoading(true);
    try {
      const response = await authApi.register({
        nome: nome.trim(),
        email: email.trim().toLowerCase(),
        cpf: cpf.replace(/\D/g, ''),
        telefone: telefone.replace(/\D/g, ''),
        password: senha,
        password_confirm: confirmarSenha,
        tipo_conta: tipoConta,
      });
      await authLogin(response.access, response.refresh, response.user);
    } catch (error: unknown) {
      const data = (error as { response?: { data?: Record<string, unknown> } })?.response?.data;
      let mensagem = 'Não foi possível criar a conta. Tente novamente.';

      if (data) {
        const firstError = Object.values(data)[0];
        if (Array.isArray(firstError) && firstError.length > 0) {
          mensagem = String(firstError[0]);
        } else if (typeof firstError === 'string') {
          mensagem = firstError;
        }
      }

      Alert.alert('Erro no cadastro', mensagem);
    } finally {
      setLoading(false);
    }
  };

  /** Limpa erro de um campo específico */
  const limparErro = (campo: string) => {
    if (errors[campo]) {
      setErrors((prev) => {
        const novo = { ...prev };
        delete novo[campo];
        return novo;
      });
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
          {/* Header */}
          <View style={styles.headerContainer}>
            <TouchableOpacity
              onPress={() => navigation.goBack()}
              style={styles.backButton}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
              <Text style={[styles.backIcon, { color: colors.text }]}>←</Text>
            </TouchableOpacity>

            <Text style={[styles.title, { color: colors.text }]}>
              Criar Conta
            </Text>
            <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
              Junte-se à comunidade Aloogaí
            </Text>
          </View>

          {/* Seletor P2P / B2B */}
          <View style={styles.tipoContainer}>
            <Text style={[styles.tipoLabel, { color: colors.text }]}>
              Tipo de conta
            </Text>
            <View
              style={[
                styles.tipoSelector,
                {
                  backgroundColor: colors.surfaceVariant,
                  borderRadius: BorderRadius.md,
                },
              ]}
            >
              {(['P2P', 'B2B'] as const).map((tipo) => (
                <TouchableOpacity
                  key={tipo}
                  onPress={() => setTipoConta(tipo)}
                  style={[
                    styles.tipoOption,
                    tipoConta === tipo && {
                      backgroundColor: BrandColors.primary,
                      borderRadius: BorderRadius.sm,
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.tipoOptionEmoji,
                    ]}
                  >
                    {tipo === 'P2P' ? '👤' : '🏢'}
                  </Text>
                  <Text
                    style={[
                      styles.tipoOptionText,
                      {
                        color: tipoConta === tipo ? BrandColors.white : colors.text,
                        fontFamily:
                          tipoConta === tipo ? FontFamily.bold : FontFamily.medium,
                      },
                    ]}
                  >
                    {tipo === 'P2P' ? 'Pessoa Física' : 'Lojista (B2B)'}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Formulário */}
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
            {/* Nome */}
            <Input
              label="Nome completo"
              placeholder="Seu nome completo"
              value={nome}
              onChangeText={(text) => {
                setNome(text);
                limparErro('nome');
              }}
              error={errors.nome}
              autoCapitalize="words"
              returnKeyType="next"
              onSubmitEditing={() => emailRef.current?.focus()}
              leftIcon={<Text style={styles.inputIcon}>👤</Text>}
              required
            />

            {/* Email */}
            <Input
              ref={emailRef}
              label="E-mail"
              placeholder="seu@email.com"
              value={email}
              onChangeText={(text) => {
                setEmail(text);
                limparErro('email');
              }}
              error={errors.email}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              returnKeyType="next"
              onSubmitEditing={() => cpfRef.current?.focus()}
              leftIcon={<Text style={styles.inputIcon}>📧</Text>}
              required
            />

            {/* CPF */}
            <Input
              ref={cpfRef}
              label="CPF"
              placeholder="000.000.000-00"
              value={cpf}
              onChangeText={(text) => {
                setCpf(mascaraCPF(text));
                limparErro('cpf');
              }}
              error={errors.cpf}
              keyboardType="numeric"
              maxLength={14}
              returnKeyType="next"
              onSubmitEditing={() => telefoneRef.current?.focus()}
              leftIcon={<Text style={styles.inputIcon}>🪪</Text>}
              required
            />

            {/* Telefone */}
            <Input
              ref={telefoneRef}
              label="Telefone"
              placeholder="(00) 00000-0000"
              value={telefone}
              onChangeText={(text) => {
                setTelefone(mascaraTelefone(text));
                limparErro('telefone');
              }}
              error={errors.telefone}
              keyboardType="phone-pad"
              maxLength={15}
              returnKeyType="next"
              onSubmitEditing={() => senhaRef.current?.focus()}
              leftIcon={<Text style={styles.inputIcon}>📱</Text>}
              required
            />

            {/* Senha */}
            <Input
              ref={senhaRef}
              label="Senha"
              placeholder="Mínimo 8 caracteres"
              value={senha}
              onChangeText={(text) => {
                setSenha(text);
                limparErro('senha');
              }}
              error={errors.senha}
              secureTextEntry={!mostrarSenha}
              returnKeyType="next"
              onSubmitEditing={() => confirmarSenhaRef.current?.focus()}
              leftIcon={<Text style={styles.inputIcon}>🔒</Text>}
              rightIcon={
                <Text style={styles.inputIcon}>
                  {mostrarSenha ? '👁️' : '🙈'}
                </Text>
              }
              onRightIconPress={() => setMostrarSenha(!mostrarSenha)}
              helperText="Letra maiúscula + número"
              required
            />

            {/* Confirmar Senha */}
            <Input
              ref={confirmarSenhaRef}
              label="Confirmar senha"
              placeholder="Repita sua senha"
              value={confirmarSenha}
              onChangeText={(text) => {
                setConfirmarSenha(text);
                limparErro('confirmarSenha');
              }}
              error={errors.confirmarSenha}
              secureTextEntry={!mostrarSenha}
              returnKeyType="done"
              onSubmitEditing={handleRegister}
              leftIcon={<Text style={styles.inputIcon}>🔐</Text>}
              required
            />

            {/* Indicador de força da senha */}
            {senha.length > 0 && (
              <View style={styles.senhaStrengthContainer}>
                <View style={styles.senhaStrengthBar}>
                  {[1, 2, 3, 4].map((level) => {
                    let filled = false;
                    if (level === 1 && senha.length >= 4) filled = true;
                    if (level === 2 && senha.length >= 8) filled = true;
                    if (level === 3 && /(?=.*[A-Z])(?=.*\d)/.test(senha)) filled = true;
                    if (level === 4 && /(?=.*[!@#$%^&*])/.test(senha) && senha.length >= 8)
                      filled = true;

                    return (
                      <View
                        key={level}
                        style={[
                          styles.senhaStrengthSegment,
                          {
                            backgroundColor: filled
                              ? level <= 2
                                ? BrandColors.accent
                                : BrandColors.success
                              : colors.surfaceVariant,
                          },
                        ]}
                      />
                    );
                  })}
                </View>
                <Text style={[styles.senhaStrengthText, { color: colors.textTertiary }]}>
                  {senha.length < 8
                    ? 'Fraca'
                    : /(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])/.test(senha)
                      ? 'Forte'
                      : /(?=.*[A-Z])(?=.*\d)/.test(senha)
                        ? 'Boa'
                        : 'Média'}
                </Text>
              </View>
            )}

            {/* Botão de registro */}
            <Button
              title="Criar Conta"
              onPress={handleRegister}
              loading={loading}
              disabled={loading}
              fullWidth
              size="lg"
              style={{ marginTop: Spacing.md }}
              testID="botao-criar-conta"
            />
          </View>

          {/* Link para login */}
          <View style={styles.loginContainer}>
            <Text style={[styles.loginText, { color: colors.textSecondary }]}>
              Já tem uma conta?{' '}
            </Text>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Text style={[styles.loginLink, { color: BrandColors.primary }]}>
                Entrar
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
    paddingBottom: Spacing.xxxl,
  },
  headerContainer: {
    marginTop: Spacing.md,
    marginBottom: Spacing.lg,
  },
  backButton: {
    marginBottom: Spacing.md,
  },
  backIcon: {
    fontSize: 28,
    fontFamily: FontFamily.bold,
  },
  title: {
    ...TextStyles.h1,
    marginBottom: Spacing.xs,
  },
  subtitle: {
    ...TextStyles.bodySmall,
  },
  tipoContainer: {
    marginBottom: Spacing.lg,
  },
  tipoLabel: {
    ...TextStyles.label,
    marginBottom: Spacing.sm,
  },
  tipoSelector: {
    flexDirection: 'row',
    padding: Spacing.xs,
    gap: Spacing.xs,
  },
  tipoOption: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.ms,
    paddingHorizontal: Spacing.sm,
    gap: Spacing.sm,
  },
  tipoOptionEmoji: {
    fontSize: 18,
  },
  tipoOptionText: {
    fontSize: FontSize.md,
  },
  formContainer: {
    borderRadius: BorderRadius.xl,
    borderWidth: 1,
    padding: Spacing.lg,
    marginBottom: Spacing.lg,
  },
  inputIcon: {
    fontSize: 18,
    opacity: 0.6,
  },
  senhaStrengthContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    marginTop: -Spacing.sm,
    marginBottom: Spacing.sm,
  },
  senhaStrengthBar: {
    flex: 1,
    flexDirection: 'row',
    gap: 4,
  },
  senhaStrengthSegment: {
    flex: 1,
    height: 4,
    borderRadius: 2,
  },
  senhaStrengthText: {
    fontSize: FontSize.xs,
    fontFamily: FontFamily.medium,
    width: 40,
  },
  loginContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: Spacing.sm,
  },
  loginText: {
    ...TextStyles.body,
  },
  loginLink: {
    ...TextStyles.bodyBold,
  },
});

export default RegisterScreen;
