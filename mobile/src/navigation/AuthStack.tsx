/**
 * AuthStack — Stack de autenticação do Aloogaí
 *
 * Contém as telas de Login e Registro.
 * Exibido quando o usuário NÃO está autenticado.
 */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import type { AuthStackParamList } from './types';
import { LoginScreen } from '../screens/auth/LoginScreen';
import { RegisterScreen } from '../screens/auth/RegisterScreen';
import { useTheme } from '../theme';

const Stack = createNativeStackNavigator<AuthStackParamList>();

/** Navigator das telas de autenticação */
export function AuthStack(): React.JSX.Element {
  const { colors } = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.background },
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
    </Stack.Navigator>
  );
}

export default AuthStack;
