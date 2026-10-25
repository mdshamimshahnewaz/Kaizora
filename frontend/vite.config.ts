import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

// Vite's SPA fallback does not resolve directory indexes in public/.
function guideDirectoryIndex(): Plugin {
  const rewrite = (request: { url?: string }, _response: unknown, next: () => void) => {
    request.url = request.url?.replace(
      /^\/user-guide\/?(?=\?|$)/,
      "/user-guide/index.html",
    );
    next();
  };
  return {
    name: "guide-directory-index",
    configureServer(server) {
      server.middlewares.use(rewrite);
    },
    configurePreviewServer(server) {
      server.middlewares.use(rewrite);
    },
  };
}

export default defineConfig({
  plugins: [guideDirectoryIndex(), react(), tailwindcss()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: false },
    },
  },
});
