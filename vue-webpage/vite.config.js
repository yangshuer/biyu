import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import esbuild from 'rollup-plugin-esbuild'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    esbuild({
      drop: ['console', 'debugger'], //打包时屏蔽打印信息的代码
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/manages': {
        // target:'https://chunfengdaozhang.com',
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/agents': {
        // target:'https://chunfengdaozhang.com',
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
