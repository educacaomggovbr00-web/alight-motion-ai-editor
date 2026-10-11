import {bundle} from '@remotion/bundler';
import {openBrowser,renderMedia,renderStill,selectComposition} from '@remotion/renderer';
import path from 'node:path';
import fs from 'node:fs';
import {readJson,writeJson} from './common';
import {validateProps,type EditProps} from '../src/schema';
export async function renderer() {
  const serveUrl=await bundle({entryPoint:path.resolve('src/index.tsx'),publicDir:path.resolve('public'),outDir:path.resolve('.bundle'),onProgress:()=>{}});
  const browserExecutable=process.env.REMOTION_BROWSER_EXECUTABLE;
  const browser=await openBrowser('chrome',{browserExecutable});
  const composition=async(p:EditProps)=>selectComposition({serveUrl,id:'EmoRap',inputProps:p,puppeteerInstance:browser});
  return {serveUrl,browser,composition,
    async video(p:EditProps,output:string) {
      const config=await composition(p);await renderMedia({serveUrl,composition:config,inputProps:p,outputLocation:output,codec:'h264',audioCodec:'aac',audioBitrate:'192k',crf:18,pixelFormat:'yuv420p',concurrency:2,puppeteerInstance:browser,logLevel:'error'});
    },
    async still(p:EditProps,frame:number,output:string) {
      await renderStill({serveUrl,composition:await composition(p),inputProps:p,frame,output,imageFormat:'png',puppeteerInstance:browser,logLevel:'error'});
    }
  };
}
if(process.argv[1]?.endsWith('render.ts')) {
  const p=validateProps(readJson('out/props.json'));const r=await renderer();
  try {await r.video(p,'out/final.mp4');writeJson('out/render.json',{engine:'Remotion',version:'4.0.534',preset:p.preset,frames:Math.round(p.duration*30),state:'renderizado'});console.log('Render Remotion concluido');}
  finally {await r.browser.close({silent:true});}
}
