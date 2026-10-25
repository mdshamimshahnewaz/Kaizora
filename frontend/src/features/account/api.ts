import { api } from "@/api/client";
import { authApi } from "@/features/auth/api";
import type { components } from "@/api/schema";
export type Account = components["schemas"]["Account"];
export type AccountUpdate = components["schemas"]["PatchedUpdateAccount"] & { version: number };
export class AccountError extends Error {
  constructor(public status: number, message: string) { super(message); }
}
export const accountApi = {
  async get(signal?: AbortSignal, organization?: string): Promise<Account> {
    const { data, response } = await api.GET("/api/v1/account/me/", { signal, cache: "no-store", params: { query: { organization } } });
    if (!data) throw new AccountError(response.status, "Unable to load your account. Please try again.");
    return data;
  },
  async update(body: AccountUpdate): Promise<Account> {
    const { data, error, response } = await api.PATCH("/api/v1/account/me/", { body, headers: { "X-CSRFToken": (await authApi.session()).csrf_token } });
    if (!data) throw new AccountError(response.status, response.status === 409 ? "Your account changed elsewhere. Your input is kept below. Review the latest saved values before saving again." : error ? Object.entries(error).map(([key, value]) => `${key}: ${String(value)}`).join(" ") : "Save outcome is uncertain. Review the latest saved values before retrying.");
    return data;
  },
};
