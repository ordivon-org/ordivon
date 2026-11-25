import {defineConfig} from "vite";
import solid from "@solidjs/vite-plugin";
export default defineConfig(({mode})=>({
  plugins:[solid()],
  base:mode==="operator"?"/_web/grants/":"/__solid_probe/",
  optimizeDeps:{exclude:["@ui-sdk/core"]},
  ...(mode==="operator"?{build:{manifest:true,outDir:"dist-operator",rollupOptions:{input:"operator.html"}}}:{}),
}));
