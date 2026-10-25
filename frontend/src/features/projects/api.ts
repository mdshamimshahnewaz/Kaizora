import { api } from "@/api/client";
import type { components } from "@/api/schema";
import { csrf, describeApiError as describe } from "@/api/request-helpers";
export type ProjectOptionKind = "members" | "roles" | "clients" | "filter_clients";
export type Project = components["schemas"]["Project"];
export type ProjectAccess = components["schemas"]["ProjectAccess"];
export type CreateProject = components["schemas"]["CreateProject"];
export type ProjectUpdate = components["schemas"]["PatchedUpdateProject"] & {version: number; reason: string};
function result<T>({data, error, response}: {data?: T; error?: unknown; response: Response}): T {
  if (data !== undefined) return data;
  throw Object.assign(new Error(describe(error) || "Request unavailable. Refresh before retrying."), {status: response.status});
}
export const projectsApi = {
  async list(org: string, page: number, search: string, status: string, type: string, client_id: string, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/projects/", {params: {path: {org}, query: {page, page_size: 50, search, ...(status ? {status} : {}), ...(type ? {type} : {}), ...(client_id ? {client_id} : {}), ordering: "name"}}, signal, cache: "no-store"}));
  },
  async get(org: string, project: string, signal?: AbortSignal) {return result(await api.GET("/api/v1/organizations/{org}/projects/{project}/", {params: {path: {org, project}}, signal, cache: "no-store"}));},
  async create(org: string, body: CreateProject) {return result(await api.POST("/api/v1/organizations/{org}/projects/", {params: {path: {org}}, body, headers: await csrf()}));},
  async update(org: string, project: string, body: ProjectUpdate) {return result(await api.PATCH("/api/v1/organizations/{org}/projects/{project}/", {params: {path: {org, project}}, body, headers: await csrf()}));},
  async transition(org: string, project: string, body: components["schemas"]["TransitionProject"]) {return result(await api.POST("/api/v1/organizations/{org}/projects/{project}/transition/", {params: {path: {org, project}}, body, headers: await csrf()}));},
  async access(org: string, project: string, page: number, signal?: AbortSignal) {return result(await api.GET("/api/v1/organizations/{org}/projects/{project}/access/", {params: {path: {org, project}, query: {page, page_size: 50}}, signal, cache: "no-store"}));},
  async grant(org: string, project: string, body: components["schemas"]["GrantProjectAccess"]) {return result(await api.POST("/api/v1/organizations/{org}/projects/{project}/access/", {params: {path: {org, project}}, body, headers: await csrf()}));},
  async end(org: string, project: string, grant: string, body: components["schemas"]["EndProjectAccess"]) {return result(await api.POST("/api/v1/organizations/{org}/projects/{project}/access/{grant}/end/", {params: {path: {org, project, grant}}, body, headers: await csrf()}));},
  async options(org: string, kind: ProjectOptionKind, page: number, search: string, project?: string, signal?: AbortSignal) {
    const query = {kind, page, page_size: 50, search};
    return project ? result(await api.GET("/api/v1/organizations/{org}/projects/{project}/options/", {params: {path: {org, project}, query}, signal, cache: "no-store"})) : result(await api.GET("/api/v1/organizations/{org}/projects/options/", {params: {path: {org}, query}, signal, cache: "no-store"}));
  },
};
