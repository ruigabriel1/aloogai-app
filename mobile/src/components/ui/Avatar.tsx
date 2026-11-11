/**
 * Componente Avatar — Imagem circular com placeholder do Aloogaí
 *
 * Exibe uma imagem de perfil circular ou, na ausência,
 * mostra as iniciais do nome do usuário.
 * Adapta automaticamente ao tema Light/Dark.
 */

import React from 'react';
import {
  View,
  Image,
  Text,
  StyleSheet,
  type ImageSourcePropType,
  type ViewStyle,
} from 'react-native';
import { useTheme } from '../../theme';
import { FontFamily } from '../../theme/typography';

/** Tamanhos pré-definidos do avatar */
export type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

/** Props do componente Avatar */
export interface AvatarProps {
  /** URI ou source da imagem */
  source?: ImageSourcePropType | string;
  /** Nome do usuário (para gerar iniciais) */
  name?: string;
  /** Tamanho do avatar (padrão: md) */
  size?: AvatarSize;
  /** Estilos adicionais */
  style?: ViewStyle;
  /** Identificador para testes */
  testID?: string;
}

/** Mapa de tamanhos em pixels */
const SIZE_MAP: Record<AvatarSize, number> = {
  xs: 28,
  sm: 36,
  md: 44,
  lg: 56,
  xl: 80,
};

/** Mapa de tamanhos de fonte para iniciais */
const FONT_SIZE_MAP: Record<AvatarSize, number> = {
  xs: 11,
  sm: 14,
  md: 16,
  lg: 20,
  xl: 28,
};

/**
 * Extrai as iniciais de um nome.
 * Ex: "João Silva" → "JS"
 */
function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (
    parts[0].charAt(0).toUpperCase() +
    parts[parts.length - 1].charAt(0).toUpperCase()
  );
}

/**
 * Gera uma cor de fundo baseada no nome (determinística).
 */
function getColorFromName(name: string): string {
  const coresAvatar = [
    '#1B7A2B', '#4CAF50', '#FF9800', '#E64A19',
    '#FFC107', '#2196F3', '#9C27B0', '#00BCD4',
    '#FF5722', '#795548',
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return coresAvatar[Math.abs(hash) % coresAvatar.length];
}

/** Avatar circular com imagem ou iniciais */
export function Avatar({
  source,
  name = '',
  size = 'md',
  style,
  testID,
}: AvatarProps): React.JSX.Element {
  const { colors } = useTheme();
  const dimension = SIZE_MAP[size];
  const fontSize = FONT_SIZE_MAP[size];

  const imageSource =
    typeof source === 'string' ? { uri: source } : source;

  const hasImage = !!source;
  const initials = getInitials(name);
  const bgColor = getColorFromName(name);

  return (
    <View
      testID={testID}
      style={[
        styles.container,
        {
          width: dimension,
          height: dimension,
          borderRadius: dimension / 2,
          backgroundColor: hasImage ? colors.surfaceVariant : bgColor,
        },
        style,
      ]}
    >
      {hasImage && imageSource ? (
        <Image
          source={imageSource}
          style={[
            styles.image,
            {
              width: dimension,
              height: dimension,
              borderRadius: dimension / 2,
            },
          ]}
          resizeMode="cover"
        />
      ) : (
        <Text
          style={[
            styles.initials,
            {
              fontSize,
              color: '#FFFFFF',
              fontFamily: FontFamily.semiBold,
            },
          ]}
        >
          {initials}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  image: {
    position: 'absolute',
  },
  initials: {
    textAlign: 'center',
  },
});

export default Avatar;
