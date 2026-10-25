import { authApi } from "@/features/auth/api";
import { api } from "@/api/client";
import type { components } from "@/api/schema";

export type Organization = components["schemas"]["Organization"];
export type OrganizationPage = components["schemas"]["OrganizationPage"];

export class OrganizationError extends Error {
  constructor(public status: number) {
    super(status === 404 || status === 403
      ? "This organization is unavailable or your access has ended."
      : "Unable to load organizations. Please try again.");
  }
}

export const organizationsApi = {
  async provisioning(signal?: AbortSignal) {
    const { data, response } = await api.GET("/api/v1/organizations/provisioning/", { signal, cache: "no-store" });
    if (!data) throw new OrganizationError(response.status);
    return data;
  },
  async create(body: components["schemas"]["CreateOrganization"]) {
    const { data, error } = await api.POST("/api/v1/organizations/", {
      body, headers: { "X-CSRFToken": (await authApi.session()).csrf_token },
    });
    if (!data) {
      const message = error ? Object.entries(error).map(([key, value]) => `${key}: ${String(value)}`).join(" ") : "Request outcome uncertain. Refresh organizations before retrying.";
      throw new Error(message);
    }
    return data;
  },
  async list(page = 1, signal?: AbortSignal): Promise<OrganizationPage> {
    const { data, response } = await api.GET("/api/v1/organizations/", {
      params: { query: { page, page_size: 50 } }, signal, cache: "no-store",
    });
    if (!data) throw new OrganizationError(response.status);
    return data;
  },
  async get(org: string, signal?: AbortSignal): Promise<Organization> {
    const { data, response } = await api.GET("/api/v1/organizations/{org}/", {
      params: { path: { org } }, signal, cache: "no-store",
    });
    if (!data) throw new OrganizationError(response.status);
    return data;
  },
};
