export const presets = ['dark-lyrics', 'emo-rap-glitch', 'big-text-impact'] as const;
export type Preset = typeof presets[number];
export type Word = {text: string; start: number; end: number; x?: number; y?: number; size?: number; color?: string; font?: 'heavy' | 'gothic' | 'mono'};
export type EditProps = {preset: Preset; intensity: number; reduceFlashes: boolean; width: number; height: number; duration: number; words: Word[]; beats: number[]; video: string; audio: string | null; demo: boolean; effects: boolean};
const fail = (message: string): never => {throw new Error(message)};
const finite = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
export function validateWords(data: unknown, duration: number): Word[] {
  if (!data || typeof data !== 'object' || !Array.isArray((data as {words?: unknown}).words)) return fail('Letras precisam de {words: [...]}');
  const words = (data as {words: unknown[]}).words;
  if (words.length > 300) fail('Maximo 300 palavras');
  let previous = -1;
  return words.map((entry) => {
    if (!entry || typeof entry !== 'object') return fail('Palavra invalida');
    const w = entry as Word;
    if (typeof w.text !== 'string' || !w.text.trim() || w.text.length > 40 || /[\x00-\x1f]/.test(w.text)) fail('Texto invalido: limite 40 caracteres');
    if (!finite(w.start) || !finite(w.end) || w.start < 0 || w.end <= w.start || w.end > duration || w.start < previous) fail('Timestamps invalidos ou fora de ordem/duracao');
    previous = w.start;
    for (const k of ['x','y'] as const) if (w[k] !== undefined && (!finite(w[k]) || w[k]! < 0.1 || w[k]! > 0.9)) fail('Posicao deve estar entre 0.1 e 0.9');
    if (w.size !== undefined && (!finite(w.size) || w.size < 0.4 || w.size > 1.6)) fail('Tamanho deve estar entre 0.4 e 1.6');
    if (w.color !== undefined && !/^#[a-f\d]{6}$/i.test(w.color)) fail('Cor deve ser hexadecimal #RRGGBB');
    if (w.font !== undefined && !['heavy','gothic','mono'].includes(w.font)) fail('Fonte invalida');
    return {text:w.text, start:w.start, end:w.end, x:w.x, y:w.y, size:w.size, color:w.color, font:w.font};
  });
}
export function validateBeats(data: unknown, duration: number): number[] {
  if (!data || typeof data !== 'object' || !Array.isArray((data as {beats?: unknown}).beats)) return fail('Batidas precisam de {beats: [segundos]}');
  const beats = (data as {beats: unknown[]}).beats;
  if (beats.length > 90) fail('Maximo 90 impactos');
  let previous = -1;
  return beats.map(v => {
    if (!finite(v) || v < 0 || v >= duration || v - previous < 0.33) return fail('Batidas invalidas; intervalo minimo 0.33s');
    previous = v; return v;
  });
}
export function validateProps(p: EditProps): EditProps {
  if (!presets.includes(p.preset) || !finite(p.duration) || p.duration < 1 || p.duration > 30) fail('Preset/duracao invalidos (1 a 30s)');
  if (![540,720,1080].includes(p.width) || p.height !== p.width / 9 * 16) fail('Resolucao invalida');
  if (!finite(p.intensity) || p.intensity < 0 || p.intensity > 1 || typeof p.reduceFlashes !== 'boolean') fail('Intensidade invalida');
  for (const src of [p.video, p.audio]) if (src !== null && !/^input\/(artist\.mp4|music\.(mp3|wav|m4a))$/.test(src)) fail('Midia deve ser local na pasta input');
  if (typeof p.video !== 'string') fail('Video obrigatorio');
  return {...p, words: validateWords({words:p.words}, p.duration), beats:validateBeats({beats:p.beats}, p.duration)};
}
export const demoProps: EditProps = {preset:'emo-rap-glitch', intensity:0.65, reduceFlashes:true, width:540, height:960, duration:4, words:[], beats:[], video:'input/artist.mp4', audio:'input/music.wav', demo:true, effects:true};
