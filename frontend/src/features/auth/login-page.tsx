import { useState } from "react";
import { Navigate, useLocation } from "react-router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  ArrowRight,
  Eye,
  EyeOff,
  Layers,
  LoaderCircle,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ThemeMenu } from "@/components/theme/theme-menu";
import { useAuth } from "./auth-provider";

const schema = z.object({
  username: z.string().trim().min(1, "Enter your username.").max(150),
  password: z.string().min(1, "Enter your password.").max(4096),
});

export function LoginPage() {
  const auth = useAuth();
  const location = useLocation();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { username: "", password: "" },
  });
  const next: unknown = location.state?.from;
  const destination =
    typeof next === "string" &&
    /^\/app(?:\/|$)/.test(next) &&
    !/[\\\r\n]/.test(next)
      ? next
      : "/app";
  if (auth.user) return <Navigate to={destination} replace />;
  return (
    <div className="grid min-h-svh lg:grid-cols-[1fr_1fr]">
      <aside className="relative hidden flex-col justify-between overflow-hidden bg-[#172554] p-12 text-white lg:flex xl:p-16">
        <div className="flex items-center gap-3 text-xl font-semibold">
          <Layers className="size-7" aria-hidden="true" />
          Kaizora
        </div>
        <div className="relative max-w-lg">
          <p className="mb-5 text-xs font-medium tracking-[0.2em] text-indigo-200">
            A CLEARER WAY TO WORK
          </p>
          <h2 className="text-4xl font-semibold leading-tight tracking-tight xl:text-5xl">
            One place for
            <br />
            what comes next.
          </h2>
          <p className="mt-6 max-w-sm text-base leading-7 text-indigo-100">
            Bring your team, projects and everyday operations into one shared
            workspace.
          </p>
          <div className="mt-10 flex gap-2" aria-hidden="true">
            <span className="h-1 w-12 rounded-full bg-teal-400" />
            <span className="h-1 w-4 rounded-full bg-white/20" />
            <span className="h-1 w-4 rounded-full bg-white/20" />
          </div>
        </div>
        <p className="text-xs text-indigo-200">
          Built for the way your team works.
        </p>
      </aside>
      <main className="flex min-w-0 flex-col bg-card px-6 py-6 sm:px-12">
        <header className="flex items-center justify-between lg:justify-end">
          <span className="flex items-center gap-2 font-semibold lg:hidden">
            <Layers className="size-5 text-primary" aria-hidden="true" />
            Kaizora
          </span>
          <ThemeMenu />
        </header>
        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center py-12">
          <div className="mb-8">
            <span className="mb-5 flex size-11 items-center justify-center rounded-xl border bg-background text-primary">
              <ShieldCheck className="size-5" aria-hidden="true" />
            </span>
            <h1 className="text-3xl font-semibold tracking-tight">
              Welcome back
            </h1>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Sign in to your Kaizora workspace.
            </p>
          </div>
          <form
            noValidate
            className="space-y-5"
            onSubmit={handleSubmit(async (values) => {
              setError("");
              try {
                await auth.signIn(values);
              } catch (cause) {
                setError(
                  cause instanceof Error && cause.name !== "TypeError"
                    ? cause.message
                    : "Unable to connect. Check your connection and try again.",
                );
              }
            })}
          >
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                {...register("username")}
                id="username"
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                className="h-11"
                placeholder="Your username"
                disabled={isSubmitting}
                aria-invalid={!!errors.username}
                aria-describedby={
                  errors.username ? "username-error" : undefined
                }
              />
              {errors.username && (
                <p id="username-error" className="text-xs text-destructive">
                  {errors.username.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  {...register("password")}
                  id="password"
                  autoComplete="current-password"
                  type={showPassword ? "text" : "password"}
                  className="h-11 pr-12"
                  placeholder="Enter your password"
                  disabled={isSubmitting}
                  aria-invalid={!!errors.password}
                  aria-describedby={
                    errors.password ? "password-error" : undefined
                  }
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1 size-9"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  aria-pressed={showPassword}
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff aria-hidden="true" />
                  ) : (
                    <Eye aria-hidden="true" />
                  )}
                </Button>
              </div>
              {errors.password && (
                <p id="password-error" className="text-xs text-destructive">
                  {errors.password.message}
                </p>
              )}
            </div>
            <Button
              type="submit"
              className="h-11 w-full"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <LoaderCircle className="animate-spin" aria-hidden="true" />
                  Signing in…
                </>
              ) : (
                <>
                  Sign in
                  <ArrowRight aria-hidden="true" />
                </>
              )}
            </Button>
          </form>
          <p className="mt-6 text-center text-xs leading-5 text-muted-foreground">
            Need access or help signing in?
            <br />
            Contact your workspace administrator.
          </p>
        </div>
        <footer className="text-center text-xs text-muted-foreground">
          Kaizora · Projects & operations
        </footer>
      </main>
    </div>
  );
}
