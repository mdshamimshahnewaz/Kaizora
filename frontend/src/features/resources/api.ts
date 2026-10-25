import { api } from "@/api/client";
import type { components } from "@/api/schema";
import { csrf, describeApiError as describe } from "@/api/request-helpers";
export type Person = components["schemas"]["Resource"];
export type Team = components["schemas"]["Team"];
export type IdentityLink = components["schemas"]["IdentityLink"];
export type TeamMembership = components["schemas"]["TeamMembership"];
function result<T>({ data, error, response }: { data?: T; error?: unknown; response: Response }): T {
  if (data !== undefined) return data;
  throw Object.assign(new Error(describe(error) || "Unable to complete the request. Refresh records before retrying."), { status: response.status });
}
export const resourcesApi = {
  async choices(org: string, kind: "members" | "resources", search: string, page: number, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/resources/choices/", { params: { path: { org }, query: { kind, search, page, page_size: 25 } }, signal, cache: "no-store" }));
  },
  async fromMember(org: string, membership_id: string) {
    return result(await api.POST("/api/v1/organizations/{org}/resources/from-member/", { params: { path: { org } }, body: { membership_id }, headers: await csrf() }));
  },
  async resources(org: string, page: number, search: string, status: string, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/resources/", { params: { path: { org }, query: { page, page_size: 50, search, ...(status ? { status } : {}) } }, signal, cache: "no-store" }));
  },
  async person(org: string, resource: string, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/resources/{resource}/", { params: { path: { org, resource } }, signal, cache: "no-store" }));
  },
  async createResource(org: string, body: components["schemas"]["ResourceCreate"]) {
    return result(await api.POST("/api/v1/organizations/{org}/resources/", { params: { path: { org } }, body, headers: await csrf() }));
  },
  async updateResource(org: string, resource: string, body: components["schemas"]["PatchedResourceUpdate"] & { version: number; reason: string }) {
    return result(await api.PATCH("/api/v1/organizations/{org}/resources/{resource}/", { params: { path: { org, resource } }, body, headers: await csrf() }));
  },
  async teams(org: string, page: number, search: string, status: string, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/teams/", { params: { path: { org }, query: { page, page_size: 50, search, ...(status ? { status } : {}) } }, signal, cache: "no-store" }));
  },
  async team(org: string, team: string, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/teams/{team}/", { params: { path: { org, team } }, signal, cache: "no-store" }));
  },
  async createTeam(org: string, body: components["schemas"]["TeamCreate"]) {
    return result(await api.POST("/api/v1/organizations/{org}/teams/", { params: { path: { org } }, body, headers: await csrf() }));
  },
  async updateTeam(org: string, team: string, body: components["schemas"]["PatchedTeamUpdate"] & { version: number; reason: string }) {
    return result(await api.PATCH("/api/v1/organizations/{org}/teams/{team}/", { params: { path: { org, team } }, body, headers: await csrf() }));
  },
  async links(org: string, resource: string, page: number, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/resources/{resource}/identity-links/", { params: { path: { org, resource }, query: { page, page_size: 50 } }, signal, cache: "no-store" }));
  },
  async link(org: string, resource: string, body: components["schemas"]["IdentityLinkCreate"]) {
    return result(await api.POST("/api/v1/organizations/{org}/resources/{resource}/identity-links/", { params: { path: { org, resource } }, body, headers: await csrf() }));
  },
  async unlink(org: string, resource: string, link: string, body: components["schemas"]["LinkEnd"]) {
    return result(await api.POST("/api/v1/organizations/{org}/resources/{resource}/identity-links/{link}/end/", { params: { path: { org, resource, link } }, body, headers: await csrf() }));
  },
  async assignments(org: string, team: string, page: number, asOf: string, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/teams/{team}/memberships/", { params: { path: { org, team }, query: { page, page_size: 50, ...(asOf ? { as_of: asOf } : {}) } }, signal, cache: "no-store" }));
  },
  async assign(org: string, team: string, body: components["schemas"]["TeamMembershipCreate"]) {
    return result(await api.POST("/api/v1/organizations/{org}/teams/{team}/memberships/", { params: { path: { org, team } }, body, headers: await csrf() }));
  },
  async end(org: string, team: string, membership: string, body: components["schemas"]["PatchedTeamMembershipEnd"] & { version: number; reason: string; end_date: string }) {
    return result(await api.PATCH("/api/v1/organizations/{org}/teams/{team}/memberships/{membership}/", { params: { path: { org, team, membership } }, body, headers: await csrf() }));
  },
};
