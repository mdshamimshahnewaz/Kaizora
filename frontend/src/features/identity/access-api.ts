import { api } from "@/api/client";
import { csrf, describeApiError as message } from "@/api/request-helpers";
import type { components } from "@/api/schema";

export type Role = components["schemas"]["Role"];
export type Member = components["schemas"]["Membership"];
export type Assignment = components["schemas"]["Assignment"];
export type Permissions = components["schemas"]["Permissions"];
export type Catalog = components["schemas"]["Catalog"];
export type RoleInput = components["schemas"]["CreateRole"];
export type RoleUpdate = components["schemas"]["PatchedUpdateRole"] & { version: number; reason: string };

function result<T>({ data, error, response }: { data?: T; error?: unknown; response: Response }): T {
  if (data !== undefined) return data;
  const detail = message(error);
  throw Object.assign(new Error(response.status === 409
    ? `${detail || "This record changed."} Refresh before trying again.`
    : detail || "Unable to complete this request. Refresh to check its outcome before retrying."), { status: response.status });
}

export const accessApi = {
  async permissions(org: string, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/permissions/me/", { params: { path: { org } }, signal, cache: "no-store" }));
  },
  async catalog(org: string, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/permissions/catalog/", { params: { path: { org } }, signal, cache: "no-store" }));
  },
  async members(org: string, page = 1, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/memberships/", { params: { path: { org }, query: { page, page_size: 50 } }, signal, cache: "no-store" }));
  },
  async roles(org: string, page = 1, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/roles/", { params: { path: { org }, query: { page, page_size: 50 } }, signal, cache: "no-store" }));
  },
  async assignments(org: string, page = 1, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/role-assignments/", { params: { path: { org }, query: { page, page_size: 50 } }, signal, cache: "no-store" }));
  },
  async addMember(org: string, body: components["schemas"]["AddMembership"]) {
    return result(await api.POST("/api/v1/organizations/{org}/memberships/", { params: { path: { org } }, body, headers: await csrf() }));
  },
  async changeMember(org: string, member: string, body: Required<components["schemas"]["PatchedChangeMembership"]>) {
    return result(await api.PATCH("/api/v1/organizations/{org}/memberships/{member}/", { params: { path: { org, member } }, body, headers: await csrf() }));
  },
  async transferOwner(org: string, body: components["schemas"]["TransferOwner"]) {
    return result(await api.POST("/api/v1/organizations/{org}/transfer-owner/", { params: { path: { org } }, body, headers: await csrf() }));
  },
  async createRole(org: string, body: components["schemas"]["CreateRole"]) {
    return result(await api.POST("/api/v1/organizations/{org}/roles/", { params: { path: { org } }, body, headers: await csrf() }));
  },
  async updateRole(org: string, role: string, body: RoleUpdate) {
    return result(await api.PATCH("/api/v1/organizations/{org}/roles/{role}/", { params: { path: { org, role } }, body, headers: await csrf() }));
  },
  async assign(org: string, body: components["schemas"]["AssignRole"]) {
    return result(await api.POST("/api/v1/organizations/{org}/role-assignments/", { params: { path: { org } }, body, headers: await csrf() }));
  },
  async revoke(org: string, assignment: string, body: components["schemas"]["Revoke"]) {
    return result(await api.POST("/api/v1/organizations/{org}/role-assignments/{assignment}/revoke/", { params: { path: { org, assignment } }, body, headers: await csrf() }));
  },
};
