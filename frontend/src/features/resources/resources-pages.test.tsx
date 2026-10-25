import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, expect, it, vi } from "vitest";
import { accessApi } from "@/features/identity/access-api";
import { organizationsApi } from "@/features/organizations/api";
import { resourcesApi, type Person, type Team } from "./api";
import { useOptionalAccount } from "@/features/account/account-provider";
import { PeoplePage, PersonDetailPage, TeamDetailPage } from "./resources-pages";

vi.mock("./api", () => ({ resourcesApi: { choices: vi.fn(), fromMember: vi.fn(), resources: vi.fn(), person: vi.fn(), createResource: vi.fn(), updateResource: vi.fn(), links: vi.fn(), link: vi.fn(), unlink: vi.fn(), team: vi.fn(), assignments: vi.fn(), assign: vi.fn(), end: vi.fn() } }));
vi.mock("@/features/account/account-provider", () => ({ useOptionalAccount: vi.fn(() => null) }));
vi.mock("@/features/identity/access-api", () => ({ accessApi: { permissions: vi.fn(), members: vi.fn() } }));
vi.mock("@/features/organizations/api", () => ({ organizationsApi: { get: vi.fn() } }));
const person: Person = { id: "person", code: "P1", display_name: "Jane", status: "active", version: 1, linked_membership_id: null };
const team: Team = { id: "team", code: "T1", name: "Delivery", status: "active", version: 1 };
function open(path = "resources") { return render(<MemoryRouter initialEntries={[`/app/o/org/${path}`]}><Routes><Route path="/app/o/:orgId/resources" element={<PeoplePage />} /><Route path="/app/o/:orgId/resources/:resourceId" element={<PersonDetailPage />} /><Route path="/app/o/:orgId/teams/:teamId" element={<TeamDetailPage />} /></Routes></MemoryRouter>); }
beforeEach(() => {
  vi.resetAllMocks(); Element.prototype.scrollIntoView = vi.fn(); Element.prototype.hasPointerCapture = vi.fn(() => false); Element.prototype.releasePointerCapture = vi.fn();
  vi.mocked(accessApi.permissions).mockResolvedValue({ organization_id: "org", membership_id: "member", is_owner: false, permissions: ["resources.read", "resources.manage", "resources.link_identity", "memberships.read", "teams.read", "teams.manage"] });
  vi.mocked(resourcesApi.resources).mockResolvedValue({ count: 1, results: [person], next: null, previous: null });
  vi.mocked(resourcesApi.person).mockResolvedValue(person);
  vi.mocked(resourcesApi.links).mockResolvedValue({ count: 0, results: [], next: null, previous: null });
  vi.mocked(resourcesApi.team).mockResolvedValue(team);
  vi.mocked(resourcesApi.assignments).mockResolvedValue({ count: 0, results: [], next: null, previous: null });
  vi.mocked(organizationsApi.get).mockResolvedValue({ id: "org", name: "Organization", timezone: "Asia/Dhaka", status: "active", version: 1, membership_id: "member", is_owner: false });
});
it("creates a no-login person from UI", async () => {
  const user = userEvent.setup(); vi.mocked(resourcesApi.createResource).mockResolvedValue(person); open();
  await user.click(await screen.findByRole("button", { name: "Create person" }));
  const form = within(screen.getByRole("dialog"));
  await user.type(form.getByLabelText("Person code"), "P1"); await user.type(form.getByLabelText("Display name"), "Jane");
  await user.click(form.getByRole("button", { name: "Create person" }));
  expect(resourcesApi.createResource).toHaveBeenCalledWith("org", { code: "P1", display_name: "Jane" });
  expect(await screen.findByText("No linked login")).toBeInTheDocument();
});
it("retains person edit draft and requires latest version review after conflict", async () => {
  const user = userEvent.setup(); vi.mocked(resourcesApi.updateResource).mockRejectedValueOnce(Object.assign(new Error("Changed elsewhere"), { status: 409 })).mockResolvedValue({ ...person, version: 3 }); open("resources/person");
  await user.click(await screen.findByRole("button", { name: "Edit person" })); const form = within(screen.getByRole("dialog"));
  await user.clear(form.getByLabelText("Display name")); await user.type(form.getByLabelText("Display name"), "My draft"); await user.type(form.getByLabelText("Reason for change"), "Rename");
  await user.click(form.getByRole("button", { name: "Edit person" })); expect(await form.findByText("Changed elsewhere")).toBeInTheDocument();
  vi.mocked(resourcesApi.person).mockResolvedValue({ ...person, version: 2, display_name: "Other edit" });
  await user.click(form.getByRole("button", { name: "Review latest version" }));
  expect(await form.findByText(/Latest: Other edit/)).toBeInTheDocument(); expect(form.getByLabelText("Display name")).toHaveValue("My draft");
  await user.click(form.getByRole("button", { name: "Edit person" })); expect(resourcesApi.updateResource).toHaveBeenLastCalledWith("org", "person", { display_name: "My draft", version: 2, reason: "Rename" });
});
it("does not expose link picker without member read permission", async () => {
  vi.mocked(accessApi.permissions).mockResolvedValue({ organization_id: "org", membership_id: "member", is_owner: false, permissions: ["resources.read", "resources.link_identity"] }); open("resources/person");
  expect(await screen.findByText("Membership read access is needed to choose a login to link.")).toBeInTheDocument(); expect(screen.queryByRole("button", { name: "Link login" })).not.toBeInTheDocument(); expect(accessApi.members).not.toHaveBeenCalled();
});
it("supports all-history review and explicit exclusive end dates", async () => {
  const user = userEvent.setup(); const row = { id: "interval", team_id: "team", resource_id: "person", resource_name: "Jane", resource_status: "retired", start_date: "2026-10-18", end_date: null, version: 1 };
  vi.mocked(resourcesApi.assignments).mockResolvedValue({ count: 1, results: [row], next: null, previous: null }); vi.mocked(resourcesApi.end).mockResolvedValue({ ...row, end_date: "2026-10-20", version: 2 }); open("teams/team");
  await user.click(await screen.findByRole("button", { name: "All history" })); expect(resourcesApi.assignments).toHaveBeenLastCalledWith("org", "team", 1, "", expect.any(AbortSignal));
  expect(await screen.findByText("Retired person")).toBeInTheDocument(); await user.click(screen.getByRole("button", { name: "Set end date" })); const form = within(screen.getByRole("dialog"));
  await user.type(form.getByLabelText("End date (exclusive)"), "2026-10-20"); await user.type(form.getByLabelText("Reason"), "Leaving"); await user.click(form.getByRole("button", { name: "Save end date" }));
  expect(resourcesApi.end).toHaveBeenCalledWith("org", "team", "interval", { end_date: "2026-10-20", reason: "Leaving", version: 1 });
});
it("hides edit form when organization access is revoked", async () => {
  const user = userEvent.setup(); open("resources/person"); await user.click(await screen.findByRole("button", { name: "Edit person" }));
  vi.mocked(accessApi.permissions).mockRejectedValue(Object.assign(new Error("Access ended"), { status: 403 })); await act(async () => window.dispatchEvent(new Event("focus")));
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument(); expect(screen.queryByText("Jane")).not.toBeInTheDocument();
});
it("keeps an unsaved person draft during a temporary background read failure", async () => {
  const user = userEvent.setup(); open("resources/person");
  await user.click(await screen.findByRole("button", { name: "Edit person" }));
  await user.clear(screen.getByLabelText("Display name"));
  await user.type(screen.getByLabelText("Display name"), "Unsaved draft");
  vi.mocked(resourcesApi.person).mockRejectedValue(new Error("Connection unavailable"));
  await act(async () => window.dispatchEvent(new Event("focus")));
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  expect(screen.getByLabelText("Display name")).toHaveValue("Unsaved draft");
});
it("uses personal timezone for link timestamps instead of the organization timezone", async () => {
  vi.mocked(useOptionalAccount).mockReturnValue({ signedIn: true, error: "", reload: vi.fn(), save: vi.fn(), account: { id: "user", username: "user", email: "", first_name: "", last_name: "", display_name: "User", version: 1, effective_timezone: "UTC", preferences: { theme: "system", timezone: "UTC" } } });
  const timestamp = "2026-10-18T18:30:00Z";
  vi.mocked(resourcesApi.links).mockResolvedValue({ count: 1, next: null, previous: null, results: [{ id: "link", resource_id: "person", membership_id: "member", started_at: timestamp, ended_at: null, reason: "Linked", resource_version: 1 }] });
  open("resources/person");
  expect(await screen.findByText(new Date(timestamp).toLocaleString(undefined, { timeZone: "UTC" }))).toBeInTheDocument();
});


it("selects an existing member directly for a team without creating a person form", async () => {
  vi.mocked(resourcesApi.choices).mockResolvedValue({ count: 1, results: [{ id: "member-rahim", label: "Rahim (@rahim)" }], next: null, previous: null });
  const user = userEvent.setup(); open("teams/team");
  await user.click(await screen.findByRole("button", { name: "Add person" }));
  await user.click(screen.getByRole("button", { name: "Choose organization member" }));
  await user.type(screen.getByRole("combobox", { name: "Search organization member" }), "rahim");
  await user.click(await screen.findByRole("option", { name: "Rahim (@rahim)" }));
  expect(screen.queryByLabelText("Person code")).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Add to team" }));
  expect(resourcesApi.assign).toHaveBeenCalledWith("org", "team", expect.objectContaining({ membership_id: "member-rahim" }));
  expect(resourcesApi.createResource).not.toHaveBeenCalled();
});

it("adds a member to People using their existing identity", async () => {
  vi.mocked(resourcesApi.choices).mockResolvedValue({ count: 1, results: [{ id: "m1", label: "Rahim (@rahim)" }], next: null, previous: null });
  vi.mocked(resourcesApi.fromMember).mockResolvedValue({ ...person, linked_membership_id: "m1" });
  const user = userEvent.setup(); open();
  await user.click(await screen.findByRole("button", { name: "Add existing member" }));
  await user.click(screen.getByRole("button", { name: "Choose organization member" }));
  await user.click(await screen.findByRole("option", { name: "Rahim (@rahim)" }));
  await user.click(screen.getByRole("button", { name: "Add member as resource" }));
  expect(resourcesApi.fromMember).toHaveBeenCalledWith("org", "m1");
});
