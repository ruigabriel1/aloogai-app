/**
 * useWebSocket — Chat em tempo real do Aloogaí
 *
 * Conecta em ws(s)://<API>/ws/chat/<locacao_id>/?token=<access JWT>.
 *
 * Protocolo (backend/apps/chat/consumers.py):
 *   cliente → servidor: {"acao": "mensagem", "conteudo": "..."} | {"acao": "digitando"} | {"acao": "marcar_lida"}
 *   servidor → cliente: {"evento": "mensagem", "mensagem": Mensagem}
 *                       {"evento": "digitando", "usuario_id": "..."}
 *                       {"evento": "lidas_atualizadas", "total": n}
 *                       {"evento": "erro", "erro": "..."}
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { WS_URL } from '../config';
import type { Mensagem } from '../api/chat';

/** Códigos de fechamento do servidor que não adianta tentar de novo */
const CODIGOS_DEFINITIVOS = new Set([4001, 4003, 4004]);
const MAX_TENTATIVAS = 5;
/** Intervalo mínimo entre dois avisos de "digitando" */
const INTERVALO_DIGITANDO_MS = 2000;
/** Quanto tempo o indicador "digitando" fica visível sem novo aviso */
const DURACAO_DIGITANDO_MS = 3000;

type EventoServidor =
  | { evento: 'mensagem'; mensagem: Mensagem }
  | { evento: 'digitando'; usuario_id: string }
  | { evento: 'lidas_atualizadas'; total: number }
  | { evento: 'erro'; erro: string };

export interface UseWebSocketReturn {
  /** Se a conexão está ativa */
  conectado: boolean;
  /** Se está tentando reconectar */
  reconectando: boolean;
  /** Mensagem de erro definitiva (ex.: sem permissão), se houver */
  erro: string | null;
  /** Mensagens recebidas em tempo real nesta sessão */
  mensagens: Mensagem[];
  /** Se a outra pessoa está digitando */
  digitando: boolean;
  /** Envia uma mensagem de texto. Devolve false se não estiver conectado. */
  enviarMensagem: (conteudo: string) => boolean;
  /** Avisa que o usuário está digitando (limitado a 1 aviso a cada 2 s) */
  enviarDigitando: () => void;
}

export function useWebSocket(locacaoId: string, ativo: boolean = true): UseWebSocketReturn {
  const token = useAuthStore((s) => s.token);

  const [conectado, setConectado] = useState(false);
  const [reconectando, setReconectando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [digitando, setDigitando] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const tentativasRef = useRef(0);
  const timerReconexaoRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const timerDigitandoRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const ultimoDigitandoRef = useRef(0);
  const encerradoRef = useRef(false);

  const tratarEvento = useCallback((evento: EventoServidor) => {
    switch (evento.evento) {
      case 'mensagem':
        setMensagens((anteriores) =>
          anteriores.some((m) => m.id === evento.mensagem.id)
            ? anteriores
            : [...anteriores, evento.mensagem],
        );
        setDigitando(false);
        break;
      case 'digitando':
        setDigitando(true);
        if (timerDigitandoRef.current) clearTimeout(timerDigitandoRef.current);
        timerDigitandoRef.current = setTimeout(() => setDigitando(false), DURACAO_DIGITANDO_MS);
        break;
      case 'erro':
        console.warn('Chat:', evento.erro);
        break;
      default:
        break;
    }
  }, []);

  const conectar = useCallback(() => {
    if (!token || !locacaoId) return;

    const ws = new WebSocket(`${WS_URL}/${locacaoId}/?token=${encodeURIComponent(token)}`);
    wsRef.current = ws;

    ws.onopen = () => {
      tentativasRef.current = 0;
      setConectado(true);
      setReconectando(false);
      setErro(null);
    };

    ws.onmessage = (e) => {
      try {
        tratarEvento(JSON.parse(String(e.data)) as EventoServidor);
      } catch {
        console.warn('Chat: evento inválido recebido');
      }
    };

    ws.onclose = (e) => {
      setConectado(false);
      wsRef.current = null;
      if (encerradoRef.current) return;

      if (CODIGOS_DEFINITIVOS.has(e.code)) {
        setReconectando(false);
        setErro(
          e.code === 4003
            ? 'Você não tem acesso a esta conversa.'
            : 'Não foi possível entrar na conversa. Faça login novamente.',
        );
        return;
      }
      if (tentativasRef.current >= MAX_TENTATIVAS) {
        setReconectando(false);
        setErro('Sem conexão com o chat.');
        return;
      }
      // Reconexão com espera crescente: 1 s, 2 s, 4 s, 8 s, 16 s
      const espera = 1000 * 2 ** tentativasRef.current;
      tentativasRef.current += 1;
      setReconectando(true);
      timerReconexaoRef.current = setTimeout(conectar, espera);
    };
  }, [token, locacaoId, tratarEvento]);

  useEffect(() => {
    if (!ativo) return undefined;
    encerradoRef.current = false;
    conectar();
    return () => {
      encerradoRef.current = true;
      if (timerReconexaoRef.current) clearTimeout(timerReconexaoRef.current);
      if (timerDigitandoRef.current) clearTimeout(timerDigitandoRef.current);
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [ativo, conectar]);

  const enviar = useCallback((dados: Record<string, string>): boolean => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return false;
    ws.send(JSON.stringify(dados));
    return true;
  }, []);

  const enviarMensagem = useCallback(
    (conteudo: string) => enviar({ acao: 'mensagem', conteudo }),
    [enviar],
  );

  const enviarDigitando = useCallback(() => {
    const agora = Date.now();
    if (agora - ultimoDigitandoRef.current < INTERVALO_DIGITANDO_MS) return;
    ultimoDigitandoRef.current = agora;
    enviar({ acao: 'digitando' });
  }, [enviar]);

  return { conectado, reconectando, erro, mensagens, digitando, enviarMensagem, enviarDigitando };
}

export default useWebSocket;
