import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, expect, it, vi } from "vitest";
import { ClientsPage } from "@/features/clients/clients-pages";
import { PeoplePage } from "@/features/resources/resources-pages";
import { clientsApi } from "@/features/clients/api";
import { resourcesApi } from "@/features/resources/api";
import { accessApi } from "@/features/identity/access-api";

vi.mock("@/features/clients/api", () => ({ clientsApi: { list: vi.fn(), create: vi.fn() } }));
vi.mock("@/features/resources/api", () => ({ resourcesApi: { resources: vi.fn(), createResource: vi.fn() } }));
vi.mock("@/features/identity/access-api", () => ({ accessApi: { permissions: vi.fn() } }));
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(accessApi.permissions).mockResolvedValue({ organization_id: "org", membership_id: "member", is_owner: true, permissions: ["clients.read", "clients.manage", "resources.read", "resources.manage"] });
});
it.each(["client", "person"] as const)("refreshes an initially empty list after creating a %s", async (kind) => {
  const user = userEvent.setup();
  const empty = { count: 0, next: null, previous: null, results: [] };
  const client = { id: "new", name: "New client", code: "NEW", status: "active" as const, version: 1, created_at: "2026-10-18T00:00:00Z" };
  const person = { id: "new", display_name: "New person", code: "NEW", status: "active" as const, version: 1, linked_membership_id: null };
  vi.mocked(clientsApi.list).mockResolvedValue(empty);
  vi.mocked(resourcesApi.resources).mockResolvedValue(empty);
  vi.mocked(clientsApi.create).mockImplementation(async () => {
    vi.mocked(clientsApi.list).mockResolvedValue({ ...empty, count: 1, results: [client] });
    return client;
  });
  vi.mocked(resourcesApi.createResource).mockImplementation(async () => {
    vi.mocked(resourcesApi.resources).mockResolvedValue({ ...empty, count: 1, results: [person] });
    return person;
  });
  const path = kind === "client" ? "clients" : "resources";
  render(<MemoryRouter initialEntries={[`/app/o/org/${path}`]}><Routes><Route path="/app/o/:orgId/clients" element={<ClientsPage />} /><Route path="/app/o/:orgId/resources" element={<PeoplePage />} /></Routes></MemoryRouter>);
  expect(await screen.findByText(/No (clients|people) match this view/)).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: `Create ${kind}` }));
  const dialog = within(screen.getByRole("dialog"));
  await user.type(dialog.getByLabelText(kind === "client" ? "Client code" : "Person code"), "NEW");
  await user.type(dialog.getByLabelText(kind === "client" ? "Client name" : "Display name"), `New ${kind}`);
  await user.click(dialog.getByRole("button", { name: `Create ${kind}` }));
  expect(await screen.findByRole("link", { name: `New ${kind}` })).toBeInTheDocument();
  expect(screen.queryByText(/No (clients|people) match this view/)).not.toBeInTheDocument();
});
