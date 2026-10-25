import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "@/app/app";
import { accountApi } from "@/features/account/api";
import { authApi } from "@/features/auth/api";

vi.mock("@/features/auth/api", () => ({
  authApi: { session: vi.fn(), login: vi.fn(), logout: vi.fn() },
}));
vi.mock("@/features/account/api", () => ({ accountApi: { get: vi.fn(), update: vi.fn() } }));
const user = {
  id: "user-id",
  username: "member",
  display_name: "Test Member",
  email: "member@example.test",
};
const anonymous = { user: null, csrf_token: "test-csrf" };
const authenticated = { user, csrf_token: "rotated-csrf" };
function open(path = "/app") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(accountApi.get).mockResolvedValue({ ...user, first_name: "Test", last_name: "Member", preferences: { theme: null, timezone: null }, version: 1, effective_timezone: "Asia/Dhaka" });
  vi.mocked(authApi.session).mockResolvedValue(anonymous);
  vi.mocked(authApi.login).mockResolvedValue(authenticated);
  vi.mocked(authApi.logout).mockResolvedValue(undefined);
});

describe("session and protected shell", () => {
  it("keeps protected UI hidden during verification and redirects anonymous users", async () => {
    let resolve!: (value: typeof anonymous) => void;
    vi.mocked(authApi.session).mockReturnValue(
      new Promise((done) => {
        resolve = done;
      }),
    );
    open("/app/account");
    expect(screen.getByRole("status")).toHaveTextContent(
      "Checking your session",
    );
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    await act(async () => resolve(anonymous));
    expect(
      await screen.findByRole("heading", { name: "Welcome back" }),
    ).toBeInTheDocument();
  });

  it("validates, signs in and returns to the requested account page", async () => {
    const actions = userEvent.setup();
    open("/app/account");
    await screen.findByRole("heading", { name: "Welcome back" });
    await actions.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByText("Enter your username.")).toBeInTheDocument();
    expect(authApi.login).not.toHaveBeenCalled();
    await actions.type(screen.getByLabelText("Username"), "member");
    await actions.type(
      screen.getByLabelText("Password", { exact: true }),
      "a-valid-password",
    );
    await actions.click(screen.getByRole("button", { name: "Sign in" }));
    expect(
      await screen.findByRole("heading", { name: "Your account" }),
    ).toBeInTheDocument();
    expect(await screen.findByLabelText("Email")).toHaveValue("member@example.test");
    expect(screen.getByLabelText("Email")).toHaveAttribute("readonly");
  });

  it("shows rejected credentials without entering the shell", async () => {
    vi.mocked(authApi.login).mockRejectedValue(
      new Error("Invalid username or password."),
    );
    const actions = userEvent.setup();
    open("/login");
    await screen.findByRole("heading", { name: "Welcome back" });
    await actions.type(screen.getByLabelText("Username"), "member");
    await actions.type(
      screen.getByLabelText("Password", { exact: true }),
      "bad-password",
    );
    await actions.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Invalid username or password.",
    );
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
  });

  it("restores a session on initial load and redirects authenticated login visits", async () => {
    vi.mocked(authApi.session).mockResolvedValue(authenticated);
    open("/login");
    expect(
      await screen.findByRole("heading", { name: "Welcome, Test Member." }),
    ).toBeInTheDocument();
  });

  it("does not pretend logout succeeded on failure, then removes the shell on success", async () => {
    vi.mocked(authApi.session).mockResolvedValue(authenticated);
    vi.mocked(authApi.logout).mockRejectedValueOnce(
      new Error("Unable to sign out. Please try again."),
    );
    const actions = userEvent.setup();
    open();
    await actions.click(
      await screen.findByRole("button", { name: "Account menu" }),
    );
    await actions.click(screen.getByRole("menuitem", { name: "Sign out" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unable to sign out",
    );
    expect(
      screen.getByRole("navigation", { name: "Main navigation" }),
    ).toBeInTheDocument();
    await actions.click(screen.getByRole("button", { name: "Account menu" }));
    await actions.click(screen.getByRole("menuitem", { name: "Sign out" }));
    expect(
      await screen.findByRole("heading", { name: "Welcome back" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
  });

  it("reconciles an expired session when the window receives focus", async () => {
    vi.mocked(authApi.session)
      .mockResolvedValueOnce(authenticated)
      .mockResolvedValue(anonymous);
    open();
    await screen.findByRole("heading", { name: "Welcome, Test Member." });
    act(() => window.dispatchEvent(new Event("focus")));
    expect(
      await screen.findByRole("heading", { name: "Welcome back" }),
    ).toBeInTheDocument();
  });

  it("offers retry when session verification fails", async () => {
    vi.mocked(authApi.session).mockRejectedValueOnce(
      new Error("Network unavailable"),
    );
    const actions = userEvent.setup();
    open();
    expect(
      await screen.findByRole("heading", { name: "Unable to connect" }),
    ).toBeInTheDocument();
    await actions.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: "Welcome back" }),
      ).toBeInTheDocument(),
    );
  });
});
