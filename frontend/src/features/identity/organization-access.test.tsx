import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { OrganizationAccess } from "./organization-access";
import { accessApi, type Role, type Member } from "./access-api";

vi.mock("./access-api", () => ({ accessApi: {
  permissions: vi.fn(), catalog: vi.fn(), members: vi.fn(), roles: vi.fn(), assignments: vi.fn(),
  addMember: vi.fn(), changeMember: vi.fn(), transferOwner: vi.fn(), createRole: vi.fn(), updateRole: vi.fn(), assign: vi.fn(), revoke: vi.fn(),
} }));
const organization = { id: "org-a", name: "Alpha", timezone: "UTC", status: "active", version: 4, membership_id: "owner-a", is_owner: true };
const role: Role = { id: "role-a", name: "Reader", scope_kind: "organization", status: "active", version: 3, permissions: ["memberships.read"] };
const member: Member = { id: "member-a", user_id: "user-a", username: "worker", display_name: "Worker", status: "active", is_owner: false, version: 2, joined_at: "2026-10-18T00:00:00Z" };
const keys = ["memberships.read", "memberships.manage", "roles.read", "roles.manage", "roles.assign"];
const empty = { count: 0, previous: null, next: null, results: [] };
const changed = vi.fn();
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(accessApi.permissions).mockResolvedValue({ organization_id: organization.id, membership_id: "owner-a", is_owner: true, permissions: keys });
  vi.mocked(accessApi.catalog).mockResolvedValue({ entries: keys.map((key) => ({ key, scope: "organization" })), presets: [] });
  vi.mocked(accessApi.members).mockResolvedValue({ ...empty, count: 1, results: [member] });
  vi.mocked(accessApi.roles).mockResolvedValue({ ...empty, count: 1, results: [role] });
  vi.mocked(accessApi.assignments).mockResolvedValue(empty);
});
function open() { render(<OrganizationAccess organization={organization} onChanged={changed} />); }

it("shows only basic membership and never fetches protected lists without grants", async () => {
  vi.mocked(accessApi.permissions).mockResolvedValue({ organization_id: organization.id, membership_id: member.id, is_owner: false, permissions: [] });
  open();
  expect(await screen.findByText(/Basic membership:/)).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Create role" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Add member" })).not.toBeInTheDocument();
  expect(accessApi.members).not.toHaveBeenCalled();
  expect(accessApi.roles).not.toHaveBeenCalled();
});

it("adds an existing username and asks its parent to reload authoritative membership", async () => {
  vi.mocked(accessApi.addMember).mockResolvedValue(member);
  const user = userEvent.setup(); open();
  await user.type(await screen.findByLabelText("Existing account username"), "worker");
  await user.click(screen.getByRole("button", { name: "Add member" }));
  expect(accessApi.addMember).toHaveBeenCalledWith("org-a", { username: "worker" });
  expect(changed).toHaveBeenCalledOnce();
});

it("creates a role using selected permissions rather than granting a hidden preset", async () => {
  vi.mocked(accessApi.createRole).mockResolvedValue(role);
  const user = userEvent.setup(); open();
  await user.click(await screen.findByRole("button", { name: "Create role" }));
  await user.type(screen.getByLabelText("Role name"), "Reader");
  await user.click(screen.getByRole("checkbox", { name: "memberships.read" }));
  await user.click(screen.getByRole("button", { name: "Save role" }));
  expect(accessApi.createRole).toHaveBeenCalledWith("org-a", { name: "Reader", scope_kind: "organization", permissions: ["memberships.read"] });
  expect(changed).toHaveBeenCalledOnce();
});

it("sends the current member version and reason, then refreshes after a conflict without replay", async () => {
  vi.mocked(accessApi.changeMember).mockRejectedValue(new Error("This record changed. Refresh before trying again."));
  const user = userEvent.setup(); open();
  await user.click(await screen.findByRole("button", { name: "Suspend" }));
  await user.type(screen.getByLabelText("Reason"), "Leave of absence");
  await user.click(screen.getByRole("button", { name: "Confirm change" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("This record changed");
  expect(accessApi.changeMember).toHaveBeenCalledExactlyOnceWith("org-a", "member-a", { status: "suspended", version: 2, reason: "Leave of absence" });
  expect(accessApi.permissions).toHaveBeenCalledTimes(2);
  expect(changed).not.toHaveBeenCalled();
});

it("confirms ownership consequences and uses the organization version", async () => {
  vi.mocked(accessApi.transferOwner).mockResolvedValue({ ...organization, is_owner: false, version: 5 });
  const user = userEvent.setup(); open();
  await user.click(await screen.findByRole("button", { name: "Transfer ownership" }));
  expect(screen.getByText(/You will stop being an owner/)).toBeInTheDocument();
  await user.type(screen.getByLabelText("Reason"), "New owner");
  await user.click(screen.getByRole("button", { name: "Confirm change" }));
  expect(accessApi.transferOwner).toHaveBeenCalledWith("org-a", { target_membership_id: "member-a", version: 4, reason: "New owner" });
});

it("removes private role content on focus when access has been revoked", async () => {
  open(); await screen.findByText("Reader");
  vi.mocked(accessApi.permissions).mockRejectedValue(new Error("Organization not found."));
  act(() => window.dispatchEvent(new Event("focus")));
  await waitFor(() => expect(screen.queryByText("Reader")).not.toBeInTheDocument());
  expect(await screen.findByRole("alert")).toHaveTextContent("Organization not found");
});
