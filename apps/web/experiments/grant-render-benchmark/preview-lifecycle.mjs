import {preview} from "vite";

/**
 * Admit an owned preview claim before the provider can acquire resources.
 * A pre-ordered native configurePreviewServer hook observes the release
 * capability even if a later setup hook rejects. If no handle is observed,
 * the claim is UNKNOWN and cannot authorize deletion of its scratch root.
 * The pinned Vite owner is responsible for the semantics of server.close():
 * it releases sockets, signal listeners and closePreviewServer hooks.
 */
export async function acquirePreview(claims, options) {
 const claim={server:null,conflict:false};
 claims.push(claim);
 const capture={
  name:"ordivon-preview-release-handle",
  enforce:"pre",
  configurePreviewServer:{
   order:"pre",
   handler(server){
    if(claim.server!==null&&claim.server!==server){
     claim.conflict=true;
     throw Error("Preview release handle identity changed");
    }
    claim.server=server;
   },
  },
 };
 const server=await preview({...options,plugins:[capture,...(options.plugins??[])]});
 if(claim.server!==null&&claim.server!==server){
  claim.conflict=true;
  throw Error("Preview release handle identity changed");
 }
 claim.server=server;
 return server;
}

/**
 * Every admitted claim receives one observed disposition. Await all native
 * owner releases, even when another release rejects. A missing/conflicting
 * handle is not a successful release; callers retain the recovery root.
 */
export function releasePreviews(claims) {
 return Promise.allSettled(claims.map(async ({server,conflict})=>{
  if(!server||conflict)throw Error("Preview acquisition release is unknown");
  await server.close();
 }));
}
