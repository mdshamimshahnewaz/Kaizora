import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useNavigate } from "react-router";
import { beforeEach, expect, it, vi } from "vitest";
import { organizationsApi, OrganizationError, type Organization } from "./api";
import { OrganizationPage, OrganizationsPage } from "./organization-pages";

vi.mock("./api", async (original) => ({
  ...await original<typeof import("./api")>(),
  organizationsApi: { list: vi.fn(), get: vi.fn(), provisioning: vi.fn(), create: vi.fn() },
}));
vi.mock("@/features/identity/access-api", () => ({ accessApi: {
  permissions: vi.fn(async () => ({ permissions: [], is_owner: false })),
  catalog: vi.fn(async () => ({ entries: [], presets: [] })),
} }));
const alpha: Organization = { id: "alpha", name: "Alpha private", timezone: "Asia/Dhaka", status: "active", version: 1, membership_id: "member-a", is_owner: true };
const beta: Organization = { ...alpha, id: "beta", name: "Beta private", membership_id: "member-b" };
function Switch() {
  const navigate = useNavigate();
  return <button onClick={() => navigate("/app/o/beta/settings")}>Switch to Beta</button>;
}
function open(path = "/app/organizations") {
  return render(<MemoryRouter initialEntries={[path]}><Switch /><Routes>
    <Route path="/app/organizations" element={<OrganizationsPage />} />
    <Route path="/app/o/:orgId/settings" element={<OrganizationPage />} />
  </Routes></MemoryRouter>);
}
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(organizationsApi.provisioning).mockResolvedValue({ can_create: false });
  vi.mocked(organizationsApi.list).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
});
it("offers account access without inventing an organization", async () => {
  open();
  expect(await screen.findByText("No organization access yet")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "My account" })).toHaveAttribute("href", "/app/account");
});
it("opens only a selected organization using an explicit route", async () => {
  vi.mocked(organizationsApi.list).mockResolvedValue({ count: 1, next: null, previous: null, results: [alpha] });
  vi.mocked(organizationsApi.get).mockResolvedValue(alpha);
  const actions = userEvent.setup();
  open();
  await actions.click(await screen.findByRole("button", { name: "Open Alpha private" }));
  expect(await screen.findByRole("heading", { name: "Organization settings" })).toBeInTheDocument();
  expect(organizationsApi.get).toHaveBeenCalledWith("alpha", expect.any(AbortSignal));
});
it("ignores a delayed response from the previous organization", async () => {
  let resolveAlpha!: (value: Organization) => void;
  vi.mocked(organizationsApi.get).mockImplementation((id) => id === "alpha"
    ? new Promise((resolve) => { resolveAlpha = resolve; }) : Promise.resolve(beta));
  const actions = userEvent.setup();
  open("/app/o/alpha/settings");
  await actions.click(screen.getByRole("button", { name: "Switch to Beta" }));
  expect(await screen.findByRole("heading", { name: "Beta private" })).toBeInTheDocument();
  await act(async () => resolveAlpha(alpha));
  expect(screen.queryByText("Alpha private")).not.toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Beta private" })).toBeInTheDocument();
});
it("clears old data immediately during organization switching", async () => {
  vi.mocked(organizationsApi.get).mockImplementation((id) => id === "alpha" ? Promise.resolve(alpha) : new Promise(() => {}));
  const actions = userEvent.setup();
  open("/app/o/alpha/settings");
  await screen.findByRole("heading", { name: "Alpha private" });
  await actions.click(screen.getByRole("button", { name: "Switch to Beta" }));
  expect(screen.queryByText("Alpha private")).not.toBeInTheDocument();
  expect(screen.getByRole("status")).toHaveTextContent("Loading organization");
});
it("removes private content when focus revalidation reports revoked access", async () => {
  vi.mocked(organizationsApi.get).mockResolvedValueOnce(alpha).mockRejectedValue(new OrganizationError(404));
  open("/app/o/alpha/settings");
  await screen.findByRole("heading", { name: "Alpha private" });
  act(() => window.dispatchEvent(new Event("focus")));
  expect(await screen.findByRole("heading", { name: "Organization unavailable" })).toBeInTheDocument();
  expect(screen.queryByText("Alpha private")).not.toBeInTheDocument();
});
it("shows an unavailable state and supports retry without false no-membership", async () => {
  vi.mocked(organizationsApi.list).mockRejectedValueOnce(new TypeError("Network failure"))
    .mockResolvedValue({ count: 1, next: null, previous: null, results: [alpha] });
  const actions = userEvent.setup();
  open();
  expect(await screen.findByRole("alert")).toHaveTextContent("Unable to connect");
  expect(screen.queryByText("No organization access yet")).not.toBeInTheDocument();
  await actions.click(screen.getByRole("button", { name: "Retry" }));
  expect(await screen.findByText("Alpha private")).toBeInTheDocument();
});
it("fetches the next bounded page", async () => {
  vi.mocked(organizationsApi.list)
    .mockResolvedValueOnce({ count: 51, previous: null, next: "/next", results: [alpha] })
    .mockResolvedValue({ count: 51, previous: "/previous", next: null, results: [beta] });
  const actions = userEvent.setup();
  open();
  await actions.click(await screen.findByRole("button", { name: "Next" }));
  expect(await screen.findByText("Beta private")).toBeInTheDocument();
  expect(screen.queryByText("Alpha private")).not.toBeInTheDocument();
  expect(organizationsApi.list).toHaveBeenLastCalledWith(2, expect.any(AbortSignal));
});

it("lets an operator create an organization and reloads its list", async () => {
  vi.mocked(organizationsApi.provisioning).mockResolvedValue({ can_create: true });
  vi.mocked(organizationsApi.create).mockResolvedValue(alpha);
  const user = userEvent.setup(); open();
  await user.click(await screen.findByRole("button", { name: "Create organization" }));
  await user.type(screen.getByLabelText("Organization name"), "Alpha private");
  await user.type(screen.getByLabelText("Owner username"), "owner");
  await user.click(screen.getByRole("button", { name: "Create" }));
  expect(organizationsApi.create).toHaveBeenCalledWith({ name: "Alpha private", timezone: "Asia/Dhaka", owner_username: "owner" });
  expect(await screen.findByText(/Alpha private created/)).toBeInTheDocument();
  expect(organizationsApi.list).toHaveBeenCalledTimes(2);
});

it("hides organization creation from ordinary members", async () => {
  open(); await screen.findByText("No organization access yet");
  expect(screen.queryByRole("button", { name: "Create organization" })).not.toBeInTheDocument();
});

it.each(["focus", "timer"])("keeps settings mounted during %s background revalidation", async (trigger) => {
  vi.useFakeTimers();
  let finish!: (value: Organization) => void;
  vi.mocked(organizationsApi.get).mockResolvedValueOnce(alpha)
    .mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
  try {
    open("/app/o/alpha/settings");
    await act(async () => {});
    const heading = screen.getByRole("heading", { name: "Alpha private" });
    await act(async () => {
      if (trigger === "focus") window.dispatchEvent(new Event("focus"));
      else vi.advanceTimersByTime(60_000);
    });
    expect(organizationsApi.get).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("heading", { name: "Alpha private" })).toBe(heading);
    expect(screen.queryByText("Loading organization…")).not.toBeInTheDocument();
    await act(async () => finish({ ...alpha, name: "Alpha refreshed" }));
    expect(screen.getByRole("heading", { name: "Alpha refreshed" })).toBe(heading);
  } finally {
    vi.useRealTimers();
  }
});
