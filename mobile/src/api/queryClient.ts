/**
 * QueryClient compartilhado (TanStack Query).
 *
 * Fica num módulo próprio para o logout poder limpar o cache:
 * sem isso, o próximo usuário via os dados do anterior.
 */

import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      /** Não refetcha automaticamente ao focar a tela */
      refetchOnWindowFocus: false,
      /** Uma nova tentativa antes de mostrar erro */
      retry: 1,
      /** Cache de 1 minuto */
      staleTime: 60 * 1000,
    },
  },
});

export default queryClient;
