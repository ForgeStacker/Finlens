import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(() => ({
  server: {
    host: "0.0.0.0", // Allow external connections (required for Docker)
    port: 5173,
    strictPort: true, // Fail if port is already in use
    hmr: {
      overlay: false,
    },
    watch: {
      usePolling: true, // Required for Docker file watching
    },
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
}));
