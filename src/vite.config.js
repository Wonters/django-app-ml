import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  root: '.',
  build: {
    outDir: resolve(__dirname, '..', 'static', 'django_app_ml', 'dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main_vue: resolve(__dirname, 'vue/main.js'),
        main_js: resolve(__dirname, 'js/main.js'),
        model_detail: resolve(__dirname, 'js/model_detail.js'),
        schema: resolve(__dirname, 'js/schema.js'),
        task: resolve(__dirname, 'js/task.js'),
        train: resolve(__dirname, 'js/train.js'),
        'dataset_analysis/main': resolve(__dirname, 'js/dataset_analysis/main.js'),
        'dataset_analysis/audit': resolve(__dirname, 'js/dataset_analysis/audit.js'),
        'dataset_analysis/ia_analysis': resolve(__dirname, 'js/dataset_analysis/ia_analysis.js'),
        'dataset_analysis/tasks': resolve(__dirname, 'js/dataset_analysis/tasks.js'),
        'css/dataset_list': resolve(__dirname, 'css/dataset_list.css'),
        'css/restframework': resolve(__dirname, 'css/restframework.css'),
        'css/user-bootstrap': resolve(__dirname, 'css/user-bootstrap.css'),
      },
      output: {
        entryFileNames: 'js/[name]-[hash].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/\.(css)$/.test(assetInfo.name)) {
            return `css/[name]-[hash].${ext}`;
          }
          return `assets/[name]-[hash].${ext}`;
        }
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/': {
        target: 'http://localhost:3000',
        changeOrigin: true
      }
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'vue')
    },
    modules: [
      resolve(__dirname, '../../bundles/node_modules'),
      'node_modules'
    ]
  }
}) 