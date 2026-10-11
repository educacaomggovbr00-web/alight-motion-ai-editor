import fs from 'node:fs';
import crypto from 'node:crypto';
import {probe,readJson,writeJson} from './common';
import type {EditProps} from '../src/schema';
export function verify(file:string,p:EditProps) {
  const d=probe(file),v=d.streams.find(s=>s.codec_type==='video'),a=d.streams.find(s=>s.codec_type==='audio');
  if(!v||v.codec_name!=='h264'||v.width!==p.width||v.height!==p.height||v.avg_frame_rate!=='30/1'||Number(v.nb_frames)!==Math.round(p.duration*30)||Math.abs(Number(d.format.duration)-Math.round(p.duration*30)/30)>.06) throw new Error('FFprobe: video diverge do contrato');
  if((p.audio && a?.codec_name!=='aac')||(!p.audio&&a)) throw new Error('FFprobe: audio diverge do contrato');
  return {state:'testado',engine:'Remotion',codec:v.codec_name,audio:a?.codec_name??null,width:v.width,height:v.height,fps:30,frames:Number(v.nb_frames),duration:Number(d.format.duration),sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')};
}
if(process.argv[1]?.endsWith('verify.ts')) {const result=verify('out/final.mp4',readJson('out/props.json'));writeJson('out/validation.json',result);console.log(JSON.stringify(result));}
