/**
 * Cliente HTTP que conversa com a API Flask do Pi.
 *
 * - injeta `Authorization: Bearer <token>` quando o token está no localStorage
 * - trata 401 redirecionando o usuário pra tela de configuração
 * - converte erros em objetos amigáveis pra UI
 */
import { API_URL } from "./config";

const TOKEN_KEY = "residuos-ai-token";

export function getToken(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(TOKEN_KEY) || "";
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  if (token) {
    window.localStorage.setItem(TOKEN_KEY, token);
  } else {
    window.localStorage.removeItem(TOKEN_KEY);
  }
}

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown, message: string) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

interface FetchOpts {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
}

export async function apiFetch<T>(
  path: string,
  opts: FetchOpts = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const url = path.startsWith("http") ? path : `${API_URL}${path}`;
  let resp: Response;
  try {
    resp = await fetch(url, {
      method: opts.method || "GET",
      headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      signal: opts.signal,
      mode: "cors",
    });
  } catch (e) {
    throw new ApiError(0, null, `Falha de rede: ${(e as Error).message}`);
  }

  let parsed: unknown = null;
  const text = await resp.text();
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }

  if (!resp.ok) {
    let msg = `HTTP ${resp.status}`;
    if (parsed && typeof parsed === "object" && "erro" in parsed) {
      msg = String((parsed as { erro: string }).erro);
    }
    throw new ApiError(resp.status, parsed, msg);
  }

  return parsed as T;
}
