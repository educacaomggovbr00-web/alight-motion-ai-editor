import {execFileSync} from 'node:child_process';
import fs from 'node:fs';
export const readJson=(path:string)=>JSON.parse(fs.readFileSync(path,'utf8'));
export const writeJson=(path:string,value:unknown)=>fs.writeFileSync(path,JSON.stringify(value,null,2));
export function probe(path:string) {
  return JSON.parse(execFileSync('ffprobe',['-v','error','-protocol_whitelist','file,pipe','-show_streams','-show_format','-of','json',path],{timeout:30000,maxBuffer:2*1024**2}).toString()) as {streams:Array<{codec_type:string; codec_name:string; width:number; height:number; avg_frame_rate:string; nb_frames:string}>;format:{duration:string;format_name:string}};
}
export const ffmpeg=(args:string[])=>execFileSync('ffmpeg',['-v','error','-y',...args],{timeout:90000,stdio:['ignore','pipe','pipe']});
