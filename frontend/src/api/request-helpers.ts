import { authApi } from "@/features/auth/api";

export function describeApiError(error: unknown): string {
  if (typeof error === "string") return error;
  if (Array.isArray(error)) return error.map(describeApiError).join(" ");
  if (error && typeof error === "object") {
    return Object.entries(error)
      .map(([key, value]) => `${key === "detail" ? "" : `${key}: `}${describeApiError(value)}`)
      .join(" ");
  }
  return "";
}

export async function csrf() {
  return { "X-CSRFToken": (await authApi.session()).csrf_token };
}
