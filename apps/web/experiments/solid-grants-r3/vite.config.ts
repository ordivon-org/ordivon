import {defineConfig} from "vite";
import solid from "@solidjs/vite-plugin";
export default defineConfig({
  plugins:[solid()],
  base:"/__solid_probe/",
  optimizeDeps:{exclude:["@ui-sdk/core"]},
});
