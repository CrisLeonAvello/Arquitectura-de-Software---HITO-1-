import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/createUser': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/createPackage': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/updateStatus': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/getTracking': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/getUsers': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/getAllPackages': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/getNotifications': {
        target: 'http://localhost:8004',
        changeOrigin: true,
      },
    },
  },
});
