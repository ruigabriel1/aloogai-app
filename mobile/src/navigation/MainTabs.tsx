/**
 * MainTabs — Navegação por tabs do Aloogaí
 *
 * Bottom Tabs: Mapa, Aluguéis, Chat, Perfil.
 * Exibido quando o usuário ESTÁ autenticado.
 * Tab ativa destacada em verde da marca.
 *
 * Wrapper com Stack Navigator para telas de detalhe
 * (ItemDetalhe, ChatRoom) que são acessíveis de
 * qualquer tab via push na stack principal.
 */

import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Text, StyleSheet, View } from 'react-native';
import type { MainTabParamList, MainStackParamList } from './types';
import { MapScreen } from '../screens/map/MapScreen';
import { RentalsScreen } from '../screens/rentals/RentalsScreen';
import { ChatListScreen } from '../screens/chat/ChatListScreen';
import { ProfileScreen } from '../screens/profile/ProfileScreen';
import { ItemDetailScreen } from '../screens/catalog/ItemDetailScreen';
import { ChatRoomScreen } from '../screens/chat/ChatRoomScreen';
import { FeedScreen } from '../screens/catalog/FeedScreen';
import { CreateItemScreen } from '../screens/catalog/CreateItemScreen';
import { MyItemsScreen } from '../screens/profile/MyItemsScreen';
import { CheckoutModal } from '../screens/rentals/CheckoutModal';
import { useTheme } from '../theme';
import { FontFamily, FontSize } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const Tab = createBottomTabNavigator<MainTabParamList>();
const Stack = createNativeStackNavigator<MainStackParamList>();

/** Ícone de tab usando emoji (substituir por ícone real na produção) */
function TabIcon({ emoji, focused, color }: { emoji: string; focused: boolean; color: string }) {
  return (
    <View style={styles.iconContainer}>
      <Text style={[styles.icon, { opacity: focused ? 1 : 0.6 }]}>
        {emoji}
      </Text>
    </View>
  );
}

/** Bottom Tabs internos (Mapa, Aluguéis, Chat, Perfil) */
function BottomTabs(): React.JSX.Element {
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();

  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.tabIconActive,
        tabBarInactiveTintColor: colors.tabIconDefault,
        tabBarStyle: {
          backgroundColor: colors.tabBarBackground,
          borderTopColor: colors.tabBarBorder,
          borderTopWidth: 1,
          height: 60 + insets.bottom,
          paddingBottom: Math.max(insets.bottom, Spacing.sm),
          paddingTop: Spacing.xs,
        },
        tabBarLabelStyle: {
          fontFamily: FontFamily.medium,
          fontSize: FontSize.xs,
          marginTop: 2,
        },
      }}
    >
      <Tab.Screen
        name="Feed"
        component={FeedScreen}
        options={{
          tabBarLabel: 'Início',
          tabBarIcon: ({ focused, color }) => (
            <TabIcon emoji="🏠" focused={focused} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Alugueis"
        component={RentalsScreen}
        options={{
          tabBarLabel: 'Aluguéis',
          tabBarIcon: ({ focused, color }) => (
            <TabIcon emoji="📋" focused={focused} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Chat"
        component={ChatListScreen}
        options={{
          tabBarLabel: 'Chat',
          tabBarIcon: ({ focused, color }) => (
            <TabIcon emoji="💬" focused={focused} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Perfil"
        component={ProfileScreen}
        options={{
          tabBarLabel: 'Perfil',
          tabBarIcon: ({ focused, color }) => (
            <TabIcon emoji="👤" focused={focused} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}

/**
 * Stack principal que envolve os Bottom Tabs.
 *
 * Permite navegar para telas de detalhe (ItemDetalhe, ChatRoom)
 * de qualquer tab sem perder as tabs no background.
 */
export function MainTabs(): React.JSX.Element {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen name="MainTabs" component={BottomTabs} />
      <Stack.Screen name="ItemDetalhe" component={ItemDetailScreen} />
      <Stack.Screen name="ChatRoom" component={ChatRoomScreen} />
      <Stack.Screen name="MapModal" component={MapScreen} options={{ presentation: 'fullScreenModal', animation: 'slide_from_bottom' }} />
      <Stack.Screen name="CreateItem" component={CreateItemScreen} options={{ title: 'Publicar Item' }} />
      <Stack.Screen name="MyItems" component={MyItemsScreen} options={{ title: 'Meus Itens' }} />
      <Stack.Screen name="CheckoutModal" component={CheckoutModal} options={{ presentation: 'modal' }} />
    </Stack.Navigator>
  );
}

const styles = StyleSheet.create({
  iconContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 28,
    height: 28,
  },
  icon: {
    fontSize: 22,
  },
});

export default MainTabs;
