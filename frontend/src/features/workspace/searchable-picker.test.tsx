import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { SearchablePicker, type ChoicePage } from "./searchable-picker";

it("searches on the server, ignores a late query response and selects with the keyboard", async () => {
  Element.prototype.scrollIntoView = vi.fn();
  let finishOld!: (value: ChoicePage) => void;
  const load = vi.fn(async (query: string) => query === "old" ? new Promise<ChoicePage>(resolve => { finishOld = resolve; }) : { count: 1, results: [{ id: query || "initial", label: query || "Initial user" }], next: null, previous: null });
  const change = vi.fn(); const user = userEvent.setup();
  render(<SearchablePicker label="Member" value={null} onChange={change} load={load} />);
  await user.click(screen.getByRole("button", { name: "Choose member" }));
  const input = screen.getByRole("combobox", { name: "Search member" });
  await user.type(input, "old");
  await waitFor(() => expect(load).toHaveBeenCalledWith("old", 1, expect.any(AbortSignal)));
  await user.clear(input); await user.type(input, "new");
  await screen.findByRole("option", { name: "new" });
  await act(async () => finishOld({ count: 1, results: [{ id: "old", label: "Obsolete user" }], next: null, previous: null }));
  expect(screen.queryByText("Obsolete user")).not.toBeInTheDocument();
  await user.keyboard("{ArrowDown}{Enter}");
  expect(change).toHaveBeenCalledWith({ id: "new", label: "new" });
});
