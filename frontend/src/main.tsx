import { StrictMode, lazy, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";
import App from "./app/app";
import "./styles.css";

const Showcase = import.meta.env.DEV
  ? lazy(() => import("./dev/ui-showcase"))
  : null;

const isShowcase = import.meta.env.DEV && window.location.pathname === "/__ui";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {isShowcase && Showcase ? (
      <Suspense
        fallback={
          <p className="p-8 text-muted-foreground">Loading UI library…</p>
        }
      >
        <Showcase />
      </Suspense>
    ) : (
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )}
  </StrictMode>,
);
