import { api } from "@/api/client";
import type { components } from "@/api/schema";

export type Session = components["schemas"]["Session"];
export type User = components["schemas"]["User"];
export type Credentials = components["schemas"]["Login"];

async function session(): Promise<Session> {
  const { data } = await api.GET("/api/v1/auth/session/", {
    cache: "no-store",
  });
  if (!data) throw new Error("Unable to check your session. Please try again.");
  return data;
}

export const authApi = {
  session,
  async login(credentials: Credentials): Promise<Session> {
    const snapshot = await session();
    const { data, error, response } = await api.POST("/api/v1/auth/login/", {
      body: credentials,
      headers: { "X-CSRFToken": snapshot.csrf_token },
    });
    if (data) return data;
    if (response.status === 429)
      throw new Error(
        "Too many sign-in attempts. Please wait a minute and try again.",
      );
    if (response.status === 403)
      throw new Error(
        "Your security token changed. Please try signing in again.",
      );
    throw new Error(error?.detail || "Unable to sign in. Please try again.");
  },
  async logout(): Promise<void> {
    const snapshot = await session();
    const { response } = await api.POST("/api/v1/auth/logout/", {
      headers: { "X-CSRFToken": snapshot.csrf_token },
    });
    if (!response.ok) throw new Error("Unable to sign out. Please try again.");
  },
};
