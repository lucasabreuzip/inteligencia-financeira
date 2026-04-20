export type JobStatus =
  | "queued"
  | "reading"
  | "cleaning"
  | "computing"
  | "persisting"
  | "ai"
  | "embedding"
  | "done"
  | "failed";

export interface JobCreatedResponse {
  job_id: string;
  status: JobStatus;
  filename: string;
}

export interface ProgressEvent {
  job_id: string;
  status: JobStatus;
  progress: number;
  message: string;
  timestamp: string;
}

export type Severity = "baixa" | "media" | "alta";
export type Classification = "saudavel" | "atencao" | "critico";

export interface AIAlert {
  titulo: string;
  severidade: Severity;
  descricao: string;
}

export interface AIInsights {
  classificacao: Classification;
  resumo: string;
  alertas: AIAlert[];
}

export interface TimeseriesPoint {
  periodo: string;
  receita: number;
  transacoes: number;
}

export interface DashboardKPIs {
  job_id: string;
  filename: string;
  total_transacoes: number;
  receita_total: number;
  ticket_medio: number;
  taxa_inadimplencia: number;
  inadimplencia_valor: number;
  periodo_inicio: string | null;
  periodo_fim: string | null;
  insights: AIInsights | null;
  timeseries: TimeseriesPoint[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatSource {
  id: string;
  valor: number;
  data: string;
  status: string;
  cliente: string;
  descricao: string;
  score: number | null;
}

export interface ToolCallLog {
  name: string;
  args: Record<string, unknown>;
  ok: boolean;
  summary: string | null;
}

export interface GroundingInfo {
  cited: string[];
  verified: string[];
  unverified: string[];
  is_grounded: boolean;
}

export interface ChatResponse {
  job_id: string;
  question: string;
  answer: string;
  sources: ChatSource[];
  tools_used: ToolCallLog[];
  grounding: GroundingInfo;
}

export interface ChatHistoryResponse {
  job_id: string;
  session_id: string;
  messages: ChatMessage[];
}

export interface Transaction {
  id: string;
  valor: number;
  data: string;
  status: string;
  cliente: string;
  descricao: string;
  categoria: string;
}

export interface TransactionsPage {
  job_id: string;
  total: number;
  offset: number;
  limit: number;
  items: Transaction[];
  categorias_disponiveis: Record<string, string>;
}

export interface AdvancedMetrics {
  fluxo_caixa: {
    meses_analisados: number;
    variacao_media_mm?: number;
    variacao_ultimo_mes?: number;
    aceleracao_ultimo_mes?: number;
    maior_queda_mm?: { mes: string; variacao: number };
    maior_alta_mm?: { mes: string; variacao: number };
    receita_ultimo_mes?: number;
    receita_mes_anterior?: number;
    serie_mensal?: { mes: string; receita: number; variacao_mm: number }[];
  };
  inadimplencia_mensal: { mes: string; taxa: number; inad_valor: number }[];
  inadimplencia_por_cliente_top5: {
    cliente: string;
    total_carteira: number;
    inad_valor: number;
    inad_qtd: number;
    taxa_inad: number;
  }[];
  inadimplencia_por_categoria: {
    categoria: string;
    total: number;
    inad: number;
    taxa_inad: number;
  }[];
  concentracao_clientes: {
    num_clientes?: number;
    hhi?: number;
    top3_share?: number;
    top10_share?: number;
    maior_cliente_share?: number;
    maior_cliente?: string;
  };
  churn_retencao: {
    mes_referencia?: string;
    mes_anterior?: string;
    clientes_ativos?: number;
    clientes_retidos?: number;
    clientes_novos?: number;
    clientes_perdidos?: number;
    taxa_retencao?: number;
    exemplos_perdidos?: string[];
  };
  outliers_valor: {
    id: string;
    cliente: string;
    valor: number;
    data: string;
    z_score: number;
    status: string;
  }[];
  dso_pendentes: {
    qtd: number;
    dso_dias: number;
    dso_maximo_dias?: number;
    valor_total: number;
  };
  comportamento_clientes?: {
    cliente: string;
    qtd_transacoes: number;
    receita_total: number;
    receita_paga: number;
    receita_em_aberto: number;
    ticket_medio: number;
    taxa_pontualidade: number;
    recencia_dias: number;
  }[];
}

export interface AdvancedInsightsResponse {
  job_id: string;
  metrics: AdvancedMetrics;
}

export interface TransactionFilters {
  status?: string;
  categoria?: string;
  cliente_contains?: string;
  min_valor?: number;
  max_valor?: number;
  data_inicio?: string;
  data_fim?: string;
  order_by?: "data" | "valor" | "cliente" | "status";
  order_dir?: "asc" | "desc";
  offset?: number;
  limit?: number;
}
