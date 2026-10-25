import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { ProjectWorkforce } from "./workforce";
import { workforceApi } from "./workforce-api";
vi.mock("./workforce-api", () => ({ workforceApi: { list: vi.fn(), options: vi.fn(), add: vi.fn(), end: vi.fn() } }));
beforeEach(() => {
  vi.resetAllMocks(); Element.prototype.scrollIntoView = vi.fn();
  Element.prototype.hasPointerCapture = vi.fn(() => false); Element.prototype.releasePointerCapture = vi.fn();
  vi.mocked(workforceApi.list).mockResolvedValue({ count: 0, results: [], next: null, previous: null });
  vi.mocked(workforceApi.options).mockImplementation(async (_org, _project, kind) => ({ count: 1, results: [{ id: kind === "members" ? "member" : "external", label: kind === "members" ? "Rahim" : "No-login contractor" }], next: null, previous: null }));
});
it.each(["members", "resources"] as const)("adds a %s worker without any access role selection", async kind => {
  const user = userEvent.setup();
  render(<ProjectWorkforce org="org" project="project" canManage archived={false} />);
  await user.click(await screen.findByRole("button", { name: "Add worker" }));
  if (kind === "resources") {
    await user.click(screen.getByRole("combobox", { name: "Worker source" }));
    await user.click(screen.getByRole("option", { name: "Existing resource / no-login worker" }));
  }
  await user.click(screen.getByRole("button", { name: kind === "members" ? "Choose organization member" : "Choose resource" }));
  await user.click(await screen.findByRole("option", { name: kind === "members" ? "Rahim" : "No-login contractor" }));
  await user.type(screen.getByLabelText("Reason"), "Delivery work");
  await user.click(screen.getByRole("button", { name: "Add worker" }));
  expect(workforceApi.add).toHaveBeenCalledWith("org", "project", { [kind === "members" ? "membership_id" : "resource_id"]: kind === "members" ? "member" : "external", reason: "Delivery work" });
  await waitFor(() => expect(workforceApi.list).toHaveBeenCalledTimes(2));
});
it("hides workforce mutations from a project reader", async () => {
  render(<ProjectWorkforce org="org" project="project" canManage={false} archived={false} />);
  await screen.findByText("No workers assigned yet.");
  expect(screen.queryByRole("button", { name: "Add worker" })).not.toBeInTheDocument();
  expect(workforceApi.options).not.toHaveBeenCalled();
});
