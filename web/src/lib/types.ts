/**
 * Tipos correspondentes às respostas JSON da API Flask
 * (api/routes.py do projeto residuos-ai).
 */

export interface StatusResponse {
  online: boolean;
  versao_api: string;
  fps: number;
  cpu_pct?: number;
  modelo: string;
  hardware: string;
  modo_degradado: boolean;
}

export interface TurnoResponse {
  ativo: boolean;
  turno?: {
    id: string;
    inicio: string;
    fim: string | null;
    contagens: Record<string, number>;
    total_frames: number;
    total_deteccoes: number;
    eventos_rejeito: string[];
  };
  contaminacao_pct?: number;
  em_alerta?: boolean;
  kg_estimados?: Record<string, number>;
  tempo_decorrido_seg?: number;
}

export interface HistoricoItem {
  id: string;
  inicio: string;
  fim: string | null;
  total_deteccoes: number;
  arquivo: string;
}

export interface CotacaoResponse {
  precos: Record<
    string,
    {
      preco_rs_kg: number;
      fonte: string;
      data: string;
      defasada: boolean;
    }
  >;
  alertas: Array<{
    material: string;
    tipo: "vender" | "aguardar";
    cor: "verde" | "amarelo";
    mensagem: string;
    variacao_pct: number;
  }>;
}

export interface CertificadoItem {
  hash: string;
  hash_curto: string;
  emissao: string;
  validade: string;
  material: string;
  quantidade_kg: number;
  arquivo_json: string;
  arquivo_pdf: string;
}

export interface CertificadoVerificacao {
  encontrado: boolean;
  verificado?: boolean;
  hash?: string;
  emissao?: string;
  validade?: string;
  emitente?: {
    cooperativa: string;
    cnpj: string;
    cidade: string;
    estado: string;
    responsavel: string;
  };
  material?: string;
  quantidade_kg?: number;
  pureza_pct?: number;
  impacto?: {
    co2_evitado_kg: number;
    agua_economizada_l: number;
    energia_kwh: number;
    arvores_equivalente: number;
  };
  mensagem?: string;
}

export interface ApiError {
  erro: string;
}
