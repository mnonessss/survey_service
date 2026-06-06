import { defineConfig, type ProxyOptions } from "vite";
import react from "@vitejs/plugin-react";

function spaBypass(req: { method?: string; headers: { accept?: string }; url?: string }) {
  const accept = req.headers.accept ?? "";
  if (req.method !== "GET" || !accept.includes("text/html")) {
    return;
  }
  const url = req.url ?? "";
  if (url.startsWith("/auth/login")) {
    return;
  }
  return "/index.html";
}

function apiProxy(): ProxyOptions {
  return {
    target: "http://localhost:8000",
    changeOrigin: true,
    bypass: spaBypass,
  };
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": apiProxy(),
      "/auth": apiProxy(),
      "/surveys": apiProxy(),
      "/integrations": apiProxy(),
      "/public": apiProxy(),
      "/uploads": apiProxy(),
      "/health": apiProxy(),
    },
  },
});
