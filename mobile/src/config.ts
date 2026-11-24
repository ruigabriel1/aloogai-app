/**
 * Configuração de ambiente do app.
 *
 * Defina no arquivo mobile/.env (veja .env.example):
 *   EXPO_PUBLIC_API_URL=http://SEU_IP_NA_REDE:8000
 *
 * No celular físico use o IP do computador na rede local (não "localhost").
 * No emulador Android, http://10.0.2.2:8000 aponta para o computador.
 */

const BASE = (process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000').replace(/\/+$/, '');

/** URL base da API REST (termina com /api/v1/). */
export const API_URL = `${BASE}/api/v1/`;

/** URL base do WebSocket do chat (ws:// ou wss://, conforme a API). */
export const WS_URL = `${BASE.replace(/^http/, 'ws')}/ws/chat`;

/** Chave publicável do Stripe (modo de teste: pk_test_...). */
export const STRIPE_PUBLISHABLE_KEY = process.env.EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY ?? '';
