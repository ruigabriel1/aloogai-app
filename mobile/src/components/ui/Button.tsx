/**
 * Componente Button — Botão principal do Aloogaí
 *
 * Variantes: primary (verde), secondary (laranja), outline, ghost.
 * Suporta estados: loading, disabled.
 * Adapta automaticamente ao tema ativo (Light/Dark).
 */

import React from 'react';
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  ViewStyle,
  TextStyle,
  type GestureResponderEvent,
} from 'react-native';
import { useTheme } from '../../theme';
import { TextStyles } from '../../theme/typography';
import { BorderRadius, Spacing } from '../../theme/spacing';
import type { ThemeColors } from '../../theme/colors';

/** Variantes visuais do botão */
export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';

/** Tamanhos do botão */
export type ButtonSize = 'sm' | 'md' | 'lg';

/** Props do componente Button */
export interface ButtonProps {
  /** Texto exibido no botão */
  title: string;
  /** Callback ao pressionar */
  onPress?: (event: GestureResponderEvent) => void;
  /** Variante visual (padrão: primary) */
  variant?: ButtonVariant;
  /** Tamanho (padrão: md) */
  size?: ButtonSize;
  /** Exibe indicador de carregamento */
  loading?: boolean;
  /** Desabilita o botão */
  disabled?: boolean;
  /** Ícone à esquerda do texto */
  leftIcon?: React.ReactNode;
  /** Ícone à direita do texto */
  rightIcon?: React.ReactNode;
  /** Ocupar largura total */
  fullWidth?: boolean;
  /** Estilos adicionais para o container */
  style?: ViewStyle;
  /** Estilos adicionais para o texto */
  textStyle?: TextStyle;
  /** Identificador para testes */
  testID?: string;
}

/**
 * Gera os estilos do botão baseado na variante e no tema.
 */
function getVariantStyles(
  variant: ButtonVariant,
  colors: ThemeColors,
  disabled: boolean,
): { container: ViewStyle; text: TextStyle; loaderColor: string } {
  const opacity = disabled ? 0.5 : 1;

  switch (variant) {
    case 'primary':
      return {
        container: {
          backgroundColor: colors.primary,
          borderWidth: 0,
          opacity,
        },
        text: { color: colors.white },
        loaderColor: colors.white,
      };
    case 'secondary':
      return {
        container: {
          backgroundColor: colors.secondary,
          borderWidth: 0,
          opacity,
        },
        text: { color: colors.white },
        loaderColor: colors.white,
      };
    case 'outline':
      return {
        container: {
          backgroundColor: 'transparent',
          borderWidth: 1.5,
          borderColor: colors.primary,
          opacity,
        },
        text: { color: colors.primary },
        loaderColor: colors.primary,
      };
    case 'ghost':
      return {
        container: {
          backgroundColor: 'transparent',
          borderWidth: 0,
          opacity,
        },
        text: { color: colors.primary },
        loaderColor: colors.primary,
      };
    default:
      return {
        container: {
          backgroundColor: colors.primary,
          borderWidth: 0,
          opacity,
        },
        text: { color: colors.white },
        loaderColor: colors.white,
      };
  }
}

/**
 * Gera os estilos do botão baseado no tamanho.
 */
function getSizeStyles(size: ButtonSize): {
  container: ViewStyle;
  text: TextStyle;
} {
  switch (size) {
    case 'sm':
      return {
        container: {
          paddingVertical: Spacing.sm,
          paddingHorizontal: Spacing.md,
          borderRadius: BorderRadius.sm,
        },
        text: { ...TextStyles.buttonSmall },
      };
    case 'md':
      return {
        container: {
          paddingVertical: Spacing.ms,
          paddingHorizontal: Spacing.lg,
          borderRadius: BorderRadius.md,
        },
        text: { ...TextStyles.button },
      };
    case 'lg':
      return {
        container: {
          paddingVertical: Spacing.md,
          paddingHorizontal: Spacing.xl,
          borderRadius: BorderRadius.lg,
        },
        text: { ...TextStyles.button, fontSize: 18 },
      };
    default:
      return {
        container: {
          paddingVertical: Spacing.ms,
          paddingHorizontal: Spacing.lg,
          borderRadius: BorderRadius.md,
        },
        text: { ...TextStyles.button },
      };
  }
}

/** Botão reutilizável com suporte a tema e variantes */
export function Button({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  style,
  textStyle,
  testID,
}: ButtonProps): React.JSX.Element {
  const { colors } = useTheme();
  const isDisabled = disabled || loading;
  const variantStyles = getVariantStyles(variant, colors, isDisabled);
  const sizeStyles = getSizeStyles(size);

  return (
    <TouchableOpacity
      testID={testID}
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={0.7}
      style={[
        styles.container,
        sizeStyles.container,
        variantStyles.container,
        fullWidth && styles.fullWidth,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator
          size="small"
          color={variantStyles.loaderColor}
          style={styles.loader}
        />
      ) : (
        <>
          {leftIcon && <>{leftIcon}</>}
          <Text
            style={[
              sizeStyles.text,
              variantStyles.text,
              leftIcon ? styles.textWithLeftIcon : undefined,
              rightIcon ? styles.textWithRightIcon : undefined,
              textStyle,
            ]}
          >
            {title}
          </Text>
          {rightIcon && <>{rightIcon}</>}
        </>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'flex-start',
  },
  fullWidth: {
    alignSelf: 'stretch',
  },
  loader: {
    marginVertical: 2,
  },
  textWithLeftIcon: {
    marginLeft: Spacing.sm,
  },
  textWithRightIcon: {
    marginRight: Spacing.sm,
  },
});

export default Button;
