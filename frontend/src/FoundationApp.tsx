import { useEffect, useState } from "react";
import { api } from "./api/client";
import "./foundation.css";

export default function FoundationApp() {
  const [status, setStatus] = useState<
    "connecting" | "connected" | "unavailable"
  >("connecting");
  useEffect(() => {
    const controller = new AbortController();
    api
      .GET("/api/v1/health/live/", { signal: controller.signal })
      .then(({ data, error }) => {
        if (!controller.signal.aborted)
          setStatus(
            !error && data?.status === "ok" ? "connected" : "unavailable",
          );
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("unavailable");
      });
    return () => controller.abort();
  }, []);
  return (
    <div className="foundation-screen">
      <main>
        <header>
          <a className="brand" href="/">
            K<span>Kaizora</span>
          </a>
          <span className="badge">Development foundation</span>
        </header>
        <section className="intro">
          <p className="eyebrow">PROJECTS + OPERATIONS</p>
          <h1>
            A shared foundation.
            <br />A clear history of work.
          </h1>
          <p className="lead">
            Project delivery, client operations, and resource management in one
            workspace.
          </p>
        </section>
        <section className="grid" aria-label="Foundation status">
          <article>
            <span className="number">01</span>
            <h2>API connection</h2>
            <p role="status" className={`status ${status}`}>
              {status === "connected"
                ? "Connected to Kaizora API"
                : status === "connecting"
                  ? "Connecting to API…"
                  : "API unavailable — start the backend"}
            </p>
            <p>Web and future mobile clients share a versioned API.</p>
          </article>
          <article>
            <span className="number">02</span>
            <h2>Module boundaries</h2>
            <p>
              Domain modules communicate through explicit Python interfaces.
            </p>
            <p>Business features will be added through their specifications.</p>
          </article>
          <article>
            <span className="number">03</span>
            <h2>Specification first</h2>
            <p>Requirements → contracts → implementation → verification.</p>
            <p>
              This is the foundation screen. Project and operations features are
              not implemented yet.
            </p>
          </article>
        </section>
        <footer>Kaizora · Foundation milestone 0001</footer>
      </main>
    </div>
  );
}
