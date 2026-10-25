import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, expect, it, vi } from "vitest";
import { accessApi } from "@/features/identity/access-api";
import { clientsApi, ClientRequestError, type Client } from "./api";
import { ClientsPage, ClientDetailPage } from "./clients-pages";

vi.mock("./api", async (original) => ({ ...await original<typeof import("./api")>(), clientsApi: {
  list: vi.fn(), get: vi.fn(), create: vi.fn(), update: vi.fn(), contacts: vi.fn(), createContact: vi.fn(), getContact: vi.fn(), updateContact: vi.fn(),
} }));
vi.mock("@/features/identity/access-api", () => ({ accessApi: { permissions: vi.fn() } }));
const client: Client = { id: "client-a", name: "Acme", code: "ACME", status: "active", version: 1, created_at: "2026-10-18T00:00:00Z" };
function open(detail = false) {
  return render(<MemoryRouter initialEntries={[`/app/o/org-a/clients${detail ? "/client-a" : ""}`]}><Routes>
    <Route path="/app/o/:orgId/clients" element={<ClientsPage />} />
    <Route path="/app/o/:orgId/clients/:clientId" element={<ClientDetailPage />} />
  </Routes></MemoryRouter>);
}
beforeEach(() => {
  vi.resetAllMocks();
  Element.prototype.scrollIntoView = vi.fn();
  Element.prototype.hasPointerCapture = vi.fn(() => false);
  Element.prototype.releasePointerCapture = vi.fn();
  vi.mocked(accessApi.permissions).mockResolvedValue({ organization_id: "org-a", membership_id: "member", is_owner: false, permissions: ["clients.read", "clients.manage", "contacts.read", "contacts.manage"] });
  vi.mocked(clientsApi.list).mockResolvedValue({ count: 1, results: [client], next: null, previous: null });
  vi.mocked(clientsApi.get).mockResolvedValue(client);
  vi.mocked(clientsApi.contacts).mockResolvedValue({ count: 0, results: [], next: null, previous: null });
});
it("creates a client from UI and refreshes actual list", async () => {
  const user = userEvent.setup();
  vi.mocked(clientsApi.create).mockResolvedValue(client);
  open();
  await user.click(await screen.findByRole("button", { name: "Create client" }));
  const form = within(screen.getByRole("dialog"));
  await user.type(form.getByLabelText("Client code"), "ACME");
  await user.type(form.getByLabelText("Client name"), "Acme");
  await user.click(form.getByRole("button", { name: "Create client" }));
  expect(clientsApi.create).toHaveBeenCalledWith("org-a", { code: "ACME", name: "Acme" });
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});
it("keeps contact PII out of requests when contact read is absent", async () => {
  vi.mocked(accessApi.permissions).mockResolvedValue({ organization_id: "org-a", membership_id: "member", is_owner: false, permissions: ["clients.read"] });
  open(true);
  expect(await screen.findByText("Contact details require separate contact read permission.")).toBeInTheDocument();
  expect(clientsApi.contacts).not.toHaveBeenCalled();
  expect(screen.queryByRole("button", { name: "Edit client" })).not.toBeInTheDocument();
});
it("retains edit draft across focus refresh and reviews conflict before retry", async () => {
  const user = userEvent.setup();
  vi.mocked(clientsApi.update).mockRejectedValueOnce(new ClientRequestError("Changed elsewhere", 409)).mockResolvedValue({ ...client, name: "My draft", version: 3 });
  open(true);
  await user.click(await screen.findByRole("button", { name: "Edit client" }));
  const form = within(screen.getByRole("dialog"));
  await user.clear(form.getByLabelText("Client name"));
  await user.type(form.getByLabelText("Client name"), "My draft");
  await user.type(form.getByLabelText("Reason for change"), "Rename");
  await act(async () => window.dispatchEvent(new Event("focus")));
  expect(form.getByLabelText("Client name")).toHaveValue("My draft");
  await user.click(form.getByRole("button", { name: "Save changes" }));
  expect(await form.findByText("Changed elsewhere")).toBeInTheDocument();
  expect(form.getByRole("button", { name: "Save changes" })).toBeDisabled();
  vi.mocked(clientsApi.get).mockResolvedValue({ ...client, name: "Someone else's edit", version: 2 });
  await user.click(form.getByRole("button", { name: "Review latest version" }));
  expect(await form.findByText(/Latest client: Someone else's edit/)).toBeInTheDocument();
  expect(form.getByLabelText("Client name")).toHaveValue("My draft");
  await user.click(form.getByRole("button", { name: "Save changes" }));
  expect(clientsApi.update).toHaveBeenLastCalledWith("org-a", "client-a", { name: "My draft", reason: "Rename", version: 2 });
});
it("does not replay an uncertain create after a refresh click", async () => {
  const user = userEvent.setup();
  vi.mocked(clientsApi.create).mockRejectedValue(new TypeError("Network lost"));
  open();
  await user.click(await screen.findByRole("button", { name: "Create client" }));
  const form = within(screen.getByRole("dialog"));
  await user.type(form.getByLabelText("Client code"), "ACME");
  await user.type(form.getByLabelText("Client name"), "Acme");
  await user.click(form.getByRole("button", { name: "Create client" }));
  await user.click(await form.findByRole("button", { name: "Refresh records" }));
  expect(form.getByRole("button", { name: "Create client" })).toBeDisabled();
  expect(clientsApi.create).toHaveBeenCalledTimes(1);
});

it("retires contacts with explicit history reason", async () => {
  const user = userEvent.setup();
  const contact = { id: "contact-a", client_id: "client-a", name: "Jane", email: "jane@example.com", phone: "", position: "Lead", status: "active" as const, version: 1 };
  vi.mocked(clientsApi.contacts).mockResolvedValue({ count: 1, results: [contact], next: null, previous: null });
  vi.mocked(clientsApi.updateContact).mockResolvedValue({ ...contact, status: "retired", version: 2 });
  open(true);
  await user.click(await screen.findByRole("button", { name: "Edit Jane" }));
  const form = within(screen.getByRole("dialog"));
  form.getByRole("combobox", { name: "Contact status" }).focus();
  await user.keyboard(" ");
  await user.click(screen.getByRole("option", { name: "Retired" }));
  await user.type(form.getByLabelText("Reason for change"), "Left company");
  await user.click(form.getByRole("button", { name: "Save contact" }));
  expect(clientsApi.updateContact).toHaveBeenCalledWith("org-a", "client-a", "contact-a", expect.objectContaining({ status: "retired", version: 1, reason: "Left company" }));
});
it("hides a private contact draft when a focus refresh reports revoked permission", async () => {
  const user = userEvent.setup();
  const contact = { id: "contact-a", client_id: "client-a", name: "Private Jane", email: "private@example.com", phone: "", position: "", status: "active" as const, version: 1 };
  vi.mocked(clientsApi.contacts).mockResolvedValue({ count: 1, results: [contact], next: null, previous: null });
  open(true);
  await user.click(await screen.findByRole("button", { name: "Edit Private Jane" }));
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  vi.mocked(accessApi.permissions).mockRejectedValue(Object.assign(new Error("Access ended"), { status: 403 }));
  await act(async () => window.dispatchEvent(new Event("focus")));
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(screen.queryByText("Private Jane")).not.toBeInTheDocument();
});

it("lets a user correct a duplicate client code without losing the draft", async () => {
  const user = userEvent.setup();
  vi.mocked(clientsApi.create)
    .mockRejectedValueOnce(new ClientRequestError("A client with this code already exists.", 409))
    .mockResolvedValue({ ...client, code: "OTHER" });
  open();
  await user.click(await screen.findByRole("button", { name: "Create client" }));
  const form = within(screen.getByRole("dialog"));
  await user.type(form.getByLabelText("Client code"), "ACME");
  await user.type(form.getByLabelText("Client name"), "Draft customer");
  await user.click(form.getByRole("button", { name: "Create client" }));
  expect(await form.findByText("A client with this code already exists.")).toBeInTheDocument();
  expect(form.getByLabelText("Client name")).toHaveValue("Draft customer");
  await user.clear(form.getByLabelText("Client code"));
  await user.type(form.getByLabelText("Client code"), "OTHER");
  await user.click(form.getByRole("button", { name: "Create client" }));
  expect(clientsApi.create).toHaveBeenLastCalledWith("org-a", { code: "OTHER", name: "Draft customer" });
});
