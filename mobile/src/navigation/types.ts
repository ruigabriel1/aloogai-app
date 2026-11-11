/**
 * Tipagem de rotas de navegação do Aloogaí
 *
 * Define os parâmetros de todas as rotas do app
 * para navegação type-safe com React Navigation.
 */

/** Parâmetros da Stack raiz (auth vs. main) */
export type RootStackParamList = {
  /** Stack de autenticação */
  Auth: undefined;
  /** Stack principal (usuário autenticado) */
  Main: undefined;
};

/** Parâmetros da Stack de autenticação */
export type AuthStackParamList = {
  /** Tela de login */
  Login: undefined;
  /** Tela de registro */
  Register: undefined;
};

/** Parâmetros das tabs principais */
export type MainTabParamList = {
  /** Tab do feed — busca por proximidade */
  Feed: undefined;
  /** Tab de aluguéis — lista de locações */
  Alugueis: undefined;
  /** Tab do chat — lista de conversas */
  Chat: undefined;
  /** Tab do perfil — dados do usuário */
  Perfil: undefined;
};

/**
 * Parâmetros das telas da stack principal (dentro do Main).
 *
 * Inclui as tabs e todas as telas acessíveis via push
 * (detalhes, chat room, etc.)
 */
export type MainStackParamList = {
  /** Bottom Tabs */
  MainTabs: undefined;
  /** Detalhes de um item do catálogo */
  ItemDetalhe: {
    itemId: string;
  };
  /** Sala de chat individual */
  ChatRoom: {
    salaId: string;
    locacaoId: string;
    nomeOutroUsuario: string;
    itemTitulo: string;
  };
  /** Modal de mapa */
  MapModal: undefined;
  /** Criar novo item */
  CreateItem: undefined;
  /** Meus Itens */
  MyItems: undefined;
  /** Modal de Checkout */
  CheckoutModal: {
    itemId: string;
    precoDiaria: number;
    valorCaucao: number;
  };
};

/**
 * Declaração global para React Navigation.
 * Permite usar useNavigation() sem especificar tipos manualmente.
 */
declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}
