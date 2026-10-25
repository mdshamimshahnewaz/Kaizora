import { api } from "@/api/client";
import type { components } from "@/api/schema";
import { csrf, describeApiError as describe } from "@/api/request-helpers";

export type Client = components["schemas"]["Client"];
export type Contact = components["schemas"]["Contact"];
export type ClientInput = components["schemas"]["CreateClient"];
export type ContactInput = components["schemas"]["CreateContact"];
export type ClientUpdate = components["schemas"]["PatchedUpdateClient"] & { version: number; reason: string };
export type ContactUpdate = components["schemas"]["PatchedUpdateContact"] & { version: number; reason: string };

export class ClientRequestError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function result<T>({ data, error, response }: { data?: T; error?: unknown; response: Response }): T {
  if (data !== undefined) return data;
  throw new ClientRequestError(response.status === 409 ? `${describe(error)} Refresh and reopen the latest record before editing.` : describe(error) || "Unable to complete the request. Refresh records before retrying.", response.status);
}

export const clientsApi = {
  async list(org: string, page: number, search: string, status: string, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/clients/", { params: { path: { org }, query: { page, page_size: 50, search, ...(status ? { status } : {}), ordering: "name" } }, signal, cache: "no-store" }));
  },
  async get(org: string, client: string, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/clients/{client}/", { params: { path: { org, client } }, signal, cache: "no-store" }));
  },
  async create(org: string, body: ClientInput) {
    return result(await api.POST("/api/v1/organizations/{org}/clients/", { params: { path: { org } }, body, headers: await csrf() }));
  },
  async update(org: string, client: string, body: ClientUpdate) {
    return result(await api.PATCH("/api/v1/organizations/{org}/clients/{client}/", { params: { path: { org, client } }, body, headers: await csrf() }));
  },
  async contacts(org: string, client: string, page: number, status: string, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/clients/{client}/contacts/", { params: { path: { org, client }, query: { page, page_size: 50, ...(status ? { status } : {}) } }, signal, cache: "no-store" }));
  },
  async getContact(org: string, client: string, contact: string, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/clients/{client}/contacts/{contact}/", { params: { path: { org, client, contact } }, signal, cache: "no-store" }));
  },
  async createContact(org: string, client: string, body: ContactInput) {
    return result(await api.POST("/api/v1/organizations/{org}/clients/{client}/contacts/", { params: { path: { org, client } }, body, headers: await csrf() }));
  },
  async updateContact(org: string, client: string, contact: string, body: ContactUpdate) {
    return result(await api.PATCH("/api/v1/organizations/{org}/clients/{client}/contacts/{contact}/", { params: { path: { org, client, contact } }, body, headers: await csrf() }));
  },
};
