import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const apiTarget = 'http://127.0.0.1:5000';
const proxyPaths = ['/login', '/profile', '/products', '/orders', '/health', '/test-error'];

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      proxyPaths.map((path) => [path, { target: apiTarget, changeOrigin: true }])
    )
  }
});