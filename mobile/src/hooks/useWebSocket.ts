/**
 * Hook de WebSocket do Aloogaí
 *
 * Gerencia conexão WebSocket para chat em tempo real.
 * URL: ws://10.0.2.2:8000/ws/chat/{locacaoId}/?token={jwt}
 *
 * Features:
 * - Reconexão automática com backoff exponencial
 * - Handlers: mensagem, digitando, lidas_atualizadas
 * - Estados: conectado, reconectando, desconectado
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuthStore } from '../store/authStore';
import type { Mensagem, Participante } from '../api/chat';

/** URL base do WebSocket (10.0.2.2 = localhost no emulador Android) */
const WS_BASE_URL = 'ws://10.0.2.2:8000/ws/chat';

/** Configurações de reconexão */
const RECONNECT_CONFIG = {
  /** Delay inicial em ms */
  initialDelay: 1000,
  /** Delay máximo em ms */
  maxDelay: 30000,
  /** Multiplicador do backoff */
  multiplier: 2,
  /** Máximo de tentativas */
  maxRetries: 10,
} as const;

/** Tipos de mensagem recebida pelo WebSocket */
type WSMensagemTipo =
  | 'mensagem'
  | 'digitando'
  | 'lidas_atualizadas'
  | 'erro';

/** Payload recebido do WebSocket */
interface WSPayload {
  tipo: WSMensagemTipo;
  mensagem?: Mensagem;
  usuario_id?: string;
  usuario_nome?: string;
  sala_id?: string;
  erro?: string;
}

/** Retorno do hook useWebSocket */
export interface UseWebSocketReturn {
  /** Se a conexão está ativa */
  conectado: boolean;
  /** Se está tentando reconectar */
  reconectando: boolean;
  /** Mensagens recebidas em tempo real */
  mensagens: Mensagem[];
  /** Quem está digitando no momento */
  digitando: Participante | null;
  /** Envia uma mensagem de texto */
  enviarMensagem: (conteudo: string) => void;
  /** Notifica que o usuário está digitando */
  enviarDigitando: () => void;
  /** Limpa as mensagens em tempo real */
  limparMensagens: () => void;
}

/**
 * Hook para conexão WebSocket com chat em tempo real.
 *
 * @param locacaoId - ID da locação vinculada à sala de chat
 * @param ativo - Se o WebSocket deve estar ativo (padrão: true)
 *
 * @example
 * ```tsx
 * const { enviarMensagem, mensagens, conectado } = useWebSocket('uuid-locacao');
 * ```
 */
export function useWebSocket(
  locacaoId: string | null,
  ativo: boolean = true,
): UseWebSocketReturn {
  const [conectado, setConectado] = useState(false);
  const [reconectando, setReconectando] = useState(false);
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [digitando, setDigitando] = useState<Participante | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const digitandoTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /** Calcula o delay com backoff exponencial */
  const getReconnectDelay = useCallback((): number => {
    const delay =
      RECONNECT_CONFIG.initialDelay *
      Math.pow(RECONNECT_CONFIG.multiplier, retryCountRef.current);
    return Math.min(delay, RECONNECT_CONFIG.maxDelay);
  }, []);

  /** Fecha a conexão WebSocket */
  const fecharConexao = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.onclose = null; // Evita reconexão ao fechar manualmente
      wsRef.current.close();
      wsRef.current = null;
    }
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    if (digitandoTimeoutRef.current) {
      clearTimeout(digitandoTimeoutRef.current);
      digitandoTimeoutRef.current = null;
    }
    setConectado(false);
    setReconectando(false);
    setDigitando(null);
  }, []);

  /** Conecta ao WebSocket */
  const conectar = useCallback(() => {
    if (!locacaoId || !ativo) return;

    const token = useAuthStore.getState().token;
    if (!token) {
      console.warn('useWebSocket — sem token JWT para conexão');
      return;
    }

    // Fecha conexão anterior se existir
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
    }

    const url = `${WS_BASE_URL}/${locacaoId}/?token=${token}`;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setConectado(true);
      setReconectando(false);
      retryCountRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data as string) as WSPayload;

        switch (payload.tipo) {
          case 'mensagem':
            if (payload.mensagem) {
              setMensagens((prev) => [...prev, payload.mensagem!]);
            }
            break;

          case 'digitando':
            if (payload.usuario_id && payload.usuario_nome) {
              setDigitando({
                id: payload.usuario_id,
                nome: payload.usuario_nome,
              });

              // Limpa o indicador após 3 segundos
              if (digitandoTimeoutRef.current) {
                clearTimeout(digitandoTimeoutRef.current);
              }
              digitandoTimeoutRef.current = setTimeout(() => {
                setDigitando(null);
              }, 3000);
            }
            break;

          case 'lidas_atualizadas':
            // Marca mensagens como lidas
            setMensagens((prev) =>
              prev.map((msg) => ({ ...msg, lida: true })),
            );
            break;

          case 'erro':
            console.error('useWebSocket — erro do servidor:', payload.erro);
            break;
        }
      } catch (err) {
        console.error('useWebSocket — erro ao parsear mensagem:', err);
      }
    };

    ws.onerror = (event) => {
      console.error('useWebSocket — erro de conexão:', event);
    };

    ws.onclose = () => {
      setConectado(false);

      // Reconexão com backoff exponencial
      if (retryCountRef.current < RECONNECT_CONFIG.maxRetries && ativo) {
        setReconectando(true);
        const delay = getReconnectDelay();
        retryCountRef.current += 1;

        retryTimeoutRef.current = setTimeout(() => {
          conectar();
        }, delay);
      } else {
        setReconectando(false);
      }
    };

    wsRef.current = ws;
  }, [locacaoId, ativo, getReconnectDelay]);

  /** Envia uma mensagem pelo WebSocket */
  const enviarMensagem = useCallback(
    (conteudo: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.warn('useWebSocket — conexão não está aberta');
        return;
      }

      wsRef.current.send(
        JSON.stringify({
          tipo: 'mensagem',
          conteudo,
        }),
      );
    },
    [],
  );

  /** Notifica que o usuário está digitando */
  const enviarDigitando = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(
      JSON.stringify({
        tipo: 'digitando',
      }),
    );
  }, []);

  /** Limpa as mensagens em tempo real */
  const limparMensagens = useCallback(() => {
    setMensagens([]);
  }, []);

  // Conecta quando locacaoId ou ativo mudam
  useEffect(() => {
    if (ativo && locacaoId) {
      conectar();
    }

    return () => {
      fecharConexao();
    };
  }, [locacaoId, ativo, conectar, fecharConexao]);

  return {
    conectado,
    reconectando,
    mensagens,
    digitando,
    enviarMensagem,
    enviarDigitando,
    limparMensagens,
  };
}

export default useWebSocket;
