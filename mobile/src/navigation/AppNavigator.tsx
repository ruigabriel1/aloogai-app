/**
 * AppNavigator — Navegador raiz do Aloogaí
 *
 * Condicional: se autenticado → MainTabs, senão → AuthStack.
 * Usa o authStore do Zustand para determinar o estado.
 */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { ActivityIndicator, View, StyleSheet } from 'react-native';
import type { RootStackParamList } from './types';
import { AuthStack } from './AuthStack';
import { MainTabs } from './MainTabs';
import { useAuthStore } from '../store/authStore';
import { useTheme } from '../theme';

const Stack = createNativeStackNavigator<RootStackParamList>();

/** Tela de carregamento enquanto verifica autenticação */
function LoadingScreen(): React.JSX.Element {
  const { colors } = useTheme();

  return (
    <View style={[styles.loading, { backgroundColor: colors.background }]}>
      <ActivityIndicator size="large" color={colors.primary} />
    </View>
  );
}

/**
 * Navegador raiz do app.
 *
 * Exibe:
 * - LoadingScreen enquanto verifica tokens salvos
 * - AuthStack se não autenticado
 * - MainTabs se autenticado
 */
export function AppNavigator(): React.JSX.Element {
  const { isAuthenticated, isLoading } = useAuthStore();
  const { colors } = useTheme();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      {isAuthenticated ? (
        <Stack.Screen name="Main" component={MainTabs} />
      ) : (
        <Stack.Screen name="Auth" component={AuthStack} />
      )}
    </Stack.Navigator>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});

export default AppNavigator;
