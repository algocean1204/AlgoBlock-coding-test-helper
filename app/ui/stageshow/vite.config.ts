import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 개발: index.html?demo=0..5|hero 를 띄워 film.mjs로 찍는다.
// 빌드: src/tour.tsx 하나를 ../tour-demos.js(IIFE, window.AlgoBlockTourDemos)와 ../tour-demos.css로 낸다.
export default defineConfig(({ command }) => ({
  plugins: [react()],
  define: command === 'build' ? { 'process.env.NODE_ENV': '"production"' } : {},
  resolve: { dedupe: ['react', 'react-dom'] },
  build: {
    target: 'es2022',
    outDir: '..',
    emptyOutDir: false,
    copyPublicDir: false,
    lib: { entry: 'src/tour.tsx', formats: ['iife'], name: 'AlgoBlockTourDemos', fileName: () => 'tour-demos.js', cssFileName: 'tour-demos' },
  },
}))
