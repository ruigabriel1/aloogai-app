/**
 * App.tsx — Entry point do app Aloogaí
 *
 * Configura:
 * - Carregamento de fontes (Inter) via expo-font
 * - SplashScreen até fontes carregarem
 * - QueryClientProvider (TanStack Query)
 * - NavigationContainer com tema adaptável (dark/light)
 * - SafeAreaProvider
 * - StatusBar com estilo adaptável ao tema
 * - Inicialização da sessão (authStore)
 */

import React, { useCallback, useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import * as SplashScreen from 'expo-splash-screen';
import * as Font from 'expo-font';
import { NavigationContainer, DefaultTheme, DarkTheme } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { StyleSheet, View } from 'react-native';
import { AppNavigator } from './src/navigation/AppNavigator';
import { useAuthStore } from './src/store/authStore';
import { useThemeMode } from './src/hooks/useThemeMode';
import { LightThemeColors, DarkThemeColors } from './src/theme/colors';

// Mantém o splash screen visível enquanto carrega recursos
SplashScreen.preventAutoHideAsync();

/** Instância do QueryClient para TanStack Query */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      /** Não refetcha automaticamente ao focar a tela */
      refetchOnWindowFocus: false,
      /** Tenta 2 vezes antes de falhar */
      retry: 2,
      /** Cache de 5 minutos */
      staleTime: 5 * 60 * 1000,
    },
  },
});

/**
 * Tema de navegação para Light mode.
 * Baseia-se no DefaultTheme do React Navigation
 * com cores da paleta Aloogaí.
 */
const AloogaiLightTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: LightThemeColors.primary,
    background: LightThemeColors.background,
    card: LightThemeColors.cardBackground,
    text: LightThemeColors.text,
    border: LightThemeColors.border,
    notification: LightThemeColors.accent,
  },
};

/**
 * Tema de navegação para Dark mode.
 * Baseia-se no DarkTheme do React Navigation
 * com cores da paleta Aloogaí.
 */
const AloogaiDarkTheme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    primary: DarkThemeColors.primary,
    background: DarkThemeColors.background,
    card: DarkThemeColors.cardBackground,
    text: DarkThemeColors.text,
    border: DarkThemeColors.border,
    notification: DarkThemeColors.accent,
  },
};

/** Componente raiz do app */
export default function App(): React.JSX.Element | null {
  const [appIsReady, setAppIsReady] = useState(false);
  const themeMode = useThemeMode();
  const isDark = themeMode === 'dark';

  useEffect(() => {
    async function prepareApp() {
      try {
        // Carrega as fontes Inter
        await Font.loadAsync({
          'Inter-Regular': require('./assets/fonts/Inter-Regular.ttf'),
          'Inter-Medium': require('./assets/fonts/Inter-Medium.ttf'),
          'Inter-SemiBold': require('./assets/fonts/Inter-SemiBold.ttf'),
          'Inter-Bold': require('./assets/fonts/Inter-Bold.ttf'),
        });

        // Inicializa a sessão de autenticação (verifica tokens salvos)
        await useAuthStore.getState().initialize();
      } catch (error) {
        console.warn('Erro ao preparar app:', error);
      } finally {
        setAppIsReady(true);
      }
    }

    prepareApp();
  }, []);

  /** Callback chamado quando o layout raiz é montado */
  const onLayoutRootView = useCallback(async () => {
    if (appIsReady) {
      // Esconde o splash screen com animação suave
      await SplashScreen.hideAsync();
    }
  }, [appIsReady]);

  if (!appIsReady) {
    return null;
  }

  return (
    <GestureHandlerRootView style={styles.flex}>
      <SafeAreaProvider>
        <QueryClientProvider client={queryClient}>
          <NavigationContainer
            theme={isDark ? AloogaiDarkTheme : AloogaiLightTheme}
          >
            <View style={styles.flex} onLayout={onLayoutRootView}>
              <AppNavigator />
              <StatusBar style={isDark ? 'light' : 'dark'} />
            </View>
          </NavigationContainer>
        </QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },
});
