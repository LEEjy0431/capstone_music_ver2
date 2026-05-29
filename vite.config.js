import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: process.env.VITE_BASE ?? '/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icon.svg', 'favicon.svg'],
      manifest: {
        name: '피아노 연주 평가',
        short_name: '피아노 평가',
        description: '악보와 음원을 업로드해 AI 피드백을 받는 피아노 연주 평가 앱',
        theme_color: '#F0B429',
        background_color: '#111111',
        display: 'standalone',
        orientation: 'portrait',
        start_url: process.env.VITE_BASE ?? '/',
        scope: process.env.VITE_BASE ?? '/',
        lang: 'ko',
        icons: [
          {
            src: 'icon.svg',
            sizes: 'any',
            type: 'image/svg+xml',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,woff,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https?:\/\/.*\/api\/.*/,
            handler: 'NetworkOnly',
          },
        ],
      },
      devOptions: {
        enabled: true,
      },
    }),
  ],
})
