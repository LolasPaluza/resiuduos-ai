/**
 * Configuração da API do Pi.
 *
 * Em dev: define no .env.local
 *   NEXT_PUBLIC_API_URL=http://10.0.1.121:5000
 *
 * Em produção (Pi servindo o web também): "" — usa caminho relativo.
 */
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

export const POLL_INTERVAL_MS = 3000;

export const CLASSES_RESIDUO = [
  "PET",
  "PEAD",
  "papel",
  "metal",
  "organico",
  "rejeito",
] as const;

export type ClasseResiduo = (typeof CLASSES_RESIDUO)[number];

export const CORES_CLASSE: Record<ClasseResiduo, string> = {
  PET: "#3498db",
  PEAD: "#e67e22",
  papel: "#f1c40f",
  metal: "#95a5a6",
  organico: "#2ecc71",
  rejeito: "#e74c3c",
};
