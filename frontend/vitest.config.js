import { defineConfig, mergeConfig } from "vitest/config"
import react from "@vitejs/plugin-react"
import viteConfig from "./vite.config.js"

export default mergeConfig(
  viteConfig,
  defineConfig({
    plugins: [react()],
    esbuild: {
      jsx: "automatic",
      jsxImportSource: "react",
    },
    test: {
      environment: "jsdom",
      setupFiles: "./src/test/setupTests.js",
    },
  })
)
