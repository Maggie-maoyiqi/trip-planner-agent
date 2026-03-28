// frontend/src/vite-env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_API_BASE_URL: "http://localhost:8000"
    readonly VITE_AMAP_JS_KEY: "4050ca7113fc39bfaf4d66fc80be1b93"
    // 如果有其他环境变量，继续添加
  }
  
  interface ImportMeta {
    readonly env: ImportMetaEnv
  }