import fs from 'node:fs';
import {ffmpeg,writeJson} from './common';
export function makeDemo() {
  fs.mkdirSync('public/input',{recursive:true});fs.mkdirSync('out',{recursive:true});
  // Apenas formas e padrões gerados; não representa artista nem música comercial.
  ffmpeg(['-f','lavfi','-i','testsrc2=size=540x960:rate=30','-t','4','-c:v','libx264','-pix_fmt','yuv420p','-an','public/input/artist.mp4']);
  ffmpeg(['-f','lavfi','-i',"aevalsrc='0.15*sin(2*PI*220*t)+0.4*exp(-45*mod(t\,0.8))*sin(2*PI*65*t)':s=48000",'-t','4','public/input/music.wav']);
  writeJson('public/input/lyrics.json',{words:[{text:'DEMO',start:.3,end:1.1},{text:'DARK',start:1.1,end:1.9,font:'gothic'},{text:'EMO',start:1.9,end:2.7,color:'#9c66ff'},{text:'IMPACT',start:2.7,end:3.8}]});
  writeJson('public/input/beats.json',{beats:[.3,1.1,1.9,2.7,3.5]});
}
if(process.argv[1]?.endsWith('demo.ts')) {makeDemo();console.log('Midia sintetica de 4 segundos criada');}
