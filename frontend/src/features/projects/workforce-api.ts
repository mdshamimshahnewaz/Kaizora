import { api } from "@/api/client";
import type { components } from "@/api/schema";
import { csrf, describeApiError } from "@/api/request-helpers";
export type Worker = components["schemas"]["ProjectWorker"];
function result<T>({ data, error, response }: { data?: T; error?: unknown; response: Response }): T {
  if (data !== undefined) return data;
  throw Object.assign(new Error(describeApiError(error) || "Unable to load workforce."), { status: response.status });
}
export const workforceApi = {
  async list(org: string, project: string, page: number, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/projects/{project}/workforce/", { params: { path: { org, project }, query: { page, page_size: 50 } }, signal, cache: "no-store" }));
  },
  async options(org: string, project: string, kind: "members" | "resources", search: string, page: number, signal?: AbortSignal) {
    return result(await api.GET("/api/v1/organizations/{org}/projects/{project}/workforce/options/", { params: { path: { org, project }, query: { kind, search, page, page_size: 25 } }, signal, cache: "no-store" }));
  },
  async add(org: string, project: string, body: components["schemas"]["AddProjectWorker"]) {
    return result(await api.POST("/api/v1/organizations/{org}/projects/{project}/workforce/", { params: { path: { org, project } }, body, headers: await csrf() }));
  },
  async end(org: string, project: string, worker: string, body: components["schemas"]["EndProjectWorker"]) {
    return result(await api.POST("/api/v1/organizations/{org}/projects/{project}/workforce/{worker}/end/", { params: { path: { org, project, worker } }, body, headers: await csrf() }));
  },
};
