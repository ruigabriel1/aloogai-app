/**
 * Hook de geolocalização do Aloogaí
 *
 * Usa expo-location para obter a posição do usuário.
 * Se a permissão for negada, retorna coordenadas padrão de São Paulo.
 */

import { useState, useEffect, useCallback } from 'react';
import * as Location from 'expo-location';

/** Coordenadas padrão de São Paulo (fallback) */
const SAO_PAULO_COORDS = {
  latitude: -23.5505,
  longitude: -46.6333,
} as const;

/** Retorno do hook useLocation */
export interface UseLocationReturn {
  /** Latitude do usuário */
  latitude: number;
  /** Longitude do usuário */
  longitude: number;
  /** Se está carregando a localização */
  loading: boolean;
  /** Mensagem de erro, se houver */
  error: string | null;
  /** Se a permissão de localização foi concedida */
  permissaoConcedida: boolean;
  /** Recarrega a localização */
  refresh: () => Promise<void>;
}

/**
 * Hook que gerencia a localização do usuário.
 *
 * - Solicita permissão de localização (foreground)
 * - Retorna coordenadas atuais ou fallback São Paulo
 * - Permite refresh manual
 *
 * @example
 * ```tsx
 * const { latitude, longitude, loading, refresh } = useLocation();
 * ```
 */
export function useLocation(): UseLocationReturn {
  const [latitude, setLatitude] = useState<number>(SAO_PAULO_COORDS.latitude);
  const [longitude, setLongitude] = useState<number>(SAO_PAULO_COORDS.longitude);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [permissaoConcedida, setPermissaoConcedida] = useState(false);

  /** Busca a localização atual do usuário */
  const fetchLocation = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Solicita permissão de localização foreground
      const { status } = await Location.requestForegroundPermissionsAsync();

      if (status !== 'granted') {
        setPermissaoConcedida(false);
        setError('Permissão de localização negada. Usando São Paulo como padrão.');
        setLatitude(SAO_PAULO_COORDS.latitude);
        setLongitude(SAO_PAULO_COORDS.longitude);
        return;
      }

      setPermissaoConcedida(true);

      // Busca posição atual com precisão balanceada
      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });

      setLatitude(location.coords.latitude);
      setLongitude(location.coords.longitude);
    } catch (err) {
      const mensagem =
        err instanceof Error ? err.message : 'Erro ao obter localização';
      setError(mensagem);
      console.error('useLocation — erro:', mensagem);

      // Fallback para São Paulo em caso de erro
      setLatitude(SAO_PAULO_COORDS.latitude);
      setLongitude(SAO_PAULO_COORDS.longitude);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLocation();
  }, [fetchLocation]);

  return {
    latitude,
    longitude,
    loading,
    error,
    permissaoConcedida,
    refresh: fetchLocation,
  };
}

export default useLocation;
