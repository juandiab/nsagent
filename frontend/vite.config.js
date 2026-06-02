import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const hostname = env.NGINX_HOSTNAME || env.VITE_NGINX_HOSTNAME

  return {
    plugins: [vue()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/nexxus-blog': {
          target: 'https://www.nexxus-tech.com',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/nexxus-blog/, '/api/blog')
        }
      },
      watch: {
        usePolling: true
      },
      ...(hostname
        ? {
            hmr: {
              protocol: 'wss',
              host: hostname,
              clientPort: 443
            }
          }
        : {})
    }
  }
})
