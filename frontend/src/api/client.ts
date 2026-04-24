const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "";

export class ApiError extends Error {
  code?: string;
  status?: number;
  details?: unknown;

  constructor(message: string, code?: string, status?: number, details?: unknown) {
    super(message);
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

type RequestOptions = RequestInit & { token?: string | null };

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) headers.set("Content-Type", "application/json");
  if (options.token) headers.set("Authorization", `Bearer ${options.token}`);

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    throw new ApiError(data?.message ?? "Request failed", data?.errorCode, response.status, data?.details);
  }
  return data as T;
}

export function asJson(body: unknown): string {
  return JSON.stringify(body);
}
