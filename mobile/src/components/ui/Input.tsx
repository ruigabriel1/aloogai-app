/**
 * Componente Input — Campo de texto estilizado do Aloogaí
 *
 * TextInput com label, placeholder, ícone, erro e suporte a tema.
 * Adapta automaticamente ao Light/Dark mode.
 */

import React, { useState, forwardRef } from 'react';
import {
  View,
  TextInput,
  Text,
  TouchableOpacity,
  StyleSheet,
  type TextInputProps,
  type ViewStyle,
} from 'react-native';
import { useTheme } from '../../theme';
import { TextStyles, FontFamily } from '../../theme/typography';
import { BorderRadius, Spacing } from '../../theme/spacing';

/** Props do componente Input */
export interface InputProps extends Omit<TextInputProps, 'style'> {
  /** Rótulo do campo */
  label?: string;
  /** Texto de placeholder */
  placeholder?: string;
  /** Mensagem de erro (exibida em vermelho) */
  error?: string;
  /** Texto de ajuda abaixo do campo */
  helperText?: string;
  /** Ícone à esquerda do campo */
  leftIcon?: React.ReactNode;
  /** Ícone à direita do campo */
  rightIcon?: React.ReactNode;
  /** Callback ao pressionar ícone direito */
  onRightIconPress?: () => void;
  /** Campo obrigatório (exibe asterisco) */
  required?: boolean;
  /** Estilos adicionais do container */
  containerStyle?: ViewStyle;
  /** Estilos adicionais do input */
  inputStyle?: ViewStyle;
  /** Identificador para testes */
  testID?: string;
}

/** Campo de texto estilizado com suporte a tema */
export const Input = forwardRef<TextInput, InputProps>(
  (
    {
      label,
      placeholder,
      error,
      helperText,
      leftIcon,
      rightIcon,
      onRightIconPress,
      required = false,
      containerStyle,
      inputStyle,
      testID,
      onFocus,
      onBlur,
      ...rest
    },
    ref,
  ) => {
    const { colors } = useTheme();
    const [isFocused, setIsFocused] = useState(false);

    const handleFocus: TextInputProps['onFocus'] = (e) => {
      setIsFocused(true);
      onFocus?.(e);
    };

    const handleBlur: TextInputProps['onBlur'] = (e) => {
      setIsFocused(false);
      onBlur?.(e);
    };

    const getBorderColor = () => {
      if (error) return colors.error;
      if (isFocused) return colors.borderFocused;
      return colors.inputBorder;
    };

    const getBackgroundColor = () => {
      if (isFocused) return colors.background;
      return colors.inputBackground;
    };

    return (
      <View style={[styles.container, containerStyle]}>
        {label && (
          <Text style={[styles.label, { color: colors.text }]}>
            {label}
            {required && (
              <Text style={{ color: colors.error }}> *</Text>
            )}
          </Text>
        )}

        <View
          style={[
            styles.inputContainer,
            {
              borderColor: getBorderColor(),
              backgroundColor: getBackgroundColor(),
            },
            isFocused && styles.inputFocused,
            error ? styles.inputError : undefined,
          ]}
        >
          {leftIcon && <View style={styles.leftIcon}>{leftIcon}</View>}

          <TextInput
            ref={ref}
            testID={testID}
            placeholder={placeholder}
            placeholderTextColor={colors.inputPlaceholder}
            onFocus={handleFocus}
            onBlur={handleBlur}
            style={[
              styles.input,
              {
                color: colors.text,
                fontFamily: FontFamily.regular,
              },
              leftIcon ? styles.inputWithLeftIcon : undefined,
              rightIcon ? styles.inputWithRightIcon : undefined,
              inputStyle,
            ]}
            {...rest}
          />

          {rightIcon && (
            <TouchableOpacity
              onPress={onRightIconPress}
              disabled={!onRightIconPress}
              style={styles.rightIcon}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
              {rightIcon}
            </TouchableOpacity>
          )}
        </View>

        {error && (
          <Text style={[styles.errorText, { color: colors.error }]}>
            {error}
          </Text>
        )}

        {helperText && !error && (
          <Text
            style={[
              styles.helperText,
              { color: colors.textSecondary },
            ]}
          >
            {helperText}
          </Text>
        )}
      </View>
    );
  },
);

Input.displayName = 'Input';

const styles = StyleSheet.create({
  container: {
    marginBottom: Spacing.md,
  },
  label: {
    ...TextStyles.label,
    marginBottom: Spacing.xs,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1.5,
    borderRadius: BorderRadius.md,
    minHeight: 52,
  },
  inputFocused: {
    borderWidth: 2,
  },
  inputError: {
    borderWidth: 2,
  },
  input: {
    flex: 1,
    fontSize: 16,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.ms,
  },
  inputWithLeftIcon: {
    paddingLeft: Spacing.xs,
  },
  inputWithRightIcon: {
    paddingRight: Spacing.xs,
  },
  leftIcon: {
    paddingLeft: Spacing.md,
  },
  rightIcon: {
    paddingRight: Spacing.md,
  },
  errorText: {
    ...TextStyles.caption,
    marginTop: Spacing.xs,
  },
  helperText: {
    ...TextStyles.caption,
    marginTop: Spacing.xs,
  },
});

export default Input;
