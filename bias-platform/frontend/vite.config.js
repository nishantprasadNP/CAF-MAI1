import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The browser calls /api/* on the same origin as the page; Vite forwards it
// to the backend. No CORS, and it works from any host/port the page loads on.
const apiProxy = {
  "/api": {
    target: process.env.API_PROXY_TARGET || "http://127.0.0.1:8000",
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, ""),
  },
};

export default defineConfig({
  plugins: [react()],
  server: { proxy: apiProxy },
  preview: { proxy: apiProxy },
});
