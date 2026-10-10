const test = require('node:test');
const assert = require('node:assert/strict');
const {createAdapter, validateJob} = require('../automation/uxp-panel/adapter.js');

function job(overrides = {}) {
    return {schema_version: 1, job_id: 'teste-001', engine: 'adobe-premiere-pro',
        style: 'Anime Shake', intensity: 'medio', export: {width: 1080, height: 1920, fps: 30,
        video_codec: 'h264', audio_codec: 'aac'}, ...overrides};
}
function runtime() {
    const state = {projectPath: 'C:\\private\\project.prproj', importAccepted: true,
        exportAccepted: true, width: 1080, height: 1920, fps: 30, extension: 'mp4',
        selections: [{}], video: true, duplicate: false, calls: []};
    const sequence = {name: 'PC-teste-001', getSettings: async () => ({
        getVideoFrameRect: async () => ({width: state.width, height: state.height}),
        getVideoFrameRate: async () => ({value: state.fps}),
    })};
    const clip = {isSequence: async () => false, getComponentChain: async () => state.video ? {} : null};
    const current = {
        get path() { return state.projectPath; },
        getSequences: async () => state.duplicate ? [sequence] : [],
        importFiles: async (...args) => { state.calls.push(['import', ...args]); return state.importAccepted; },
        createSequenceFromMedia: async (...args) => { state.calls.push(['sequence', ...args]); return sequence; },
        setActiveSequence: async () => true,
        getActiveSequence: async () => sequence,
        save: async () => true,
    };
    const ppro = {
        Project: {getActiveProject: async () => current},
        ProjectUtils: {getSelection: async () => ({getItems: async () => state.selections})},
        ClipProjectItem: {cast: () => clip},
        Constants: {ExportType: {IMMEDIATELY: 'HOST_IMMEDIATE'}, MediaType: {VIDEO: 'VIDEO'}},
        EncoderManager: {getExportFileExtension: async () => state.extension, getManager: () => ({
            exportSequence: async (...args) => {state.calls.push(['export', ...args]); return state.exportAccepted;},
        })},
    };
    const adapter = createAdapter(ppro, '26.5.2-test-double');
    return {state, adapter};
}

test('rejeita ID inseguro e formato inválido antes de chamar o host', () => {
    for (const id of ['../private', 'a/b', '$(whoami)', '']) {
        assert.throws(() => validateJob(job({job_id: id})), /inválido/);
    }
    assert.throws(() => validateJob(job({export: {width: 720, height: 1280, fps: 30}})), /Formato/);
});

test('whitelist descarta segredos e caminhos desconhecidos', () => {
    const value = validateJob(job({token: 'DO-NOT-PUBLISH', path: 'C:\\private', secret: {password: 'hidden'}}));
    assert.ok(!JSON.stringify(value).includes('DO-NOT-PUBLISH'));
    assert.ok(!Object.hasOwn(value, 'path'));
});

test('não permite operação sem tarefa ou troca silenciosa de projeto', async () => {
    const {state, adapter} = runtime();
    await assert.rejects(adapter.inspect(), /Carregue/);
    adapter.load(job());
    await adapter.inspect();
    state.projectPath = 'C:\\different.prproj';
    await assert.rejects(adapter.saveProject(), /mudou/);
});

test('importação recusada não gera observação de sucesso', async () => {
    const {state, adapter} = runtime();
    adapter.load(job()); state.importAccepted = false;
    await assert.rejects(adapter.importMedia([{isFile: true, nativePath: 'C:\\private\\video.mp4'}]), /não confirmou/);
    assert.equal(adapter.report().observations.length, 1);
});

test('recusa seleção múltipla, áudio sem vídeo e sequência duplicada', async () => {
    const {state, adapter} = runtime(); adapter.load(job());
    state.selections = [{}, {}];
    await assert.rejects(adapter.createSequence(), /exatamente um/);
    state.selections = [{}]; state.video = false;
    await assert.rejects(adapter.createSequence(), /não possui vídeo/);
    state.video = true; state.duplicate = true;
    await assert.rejects(adapter.createSequence(), /já existe/);
    assert.equal(state.calls.length, 0);
});

test('exportação é bloqueada com resolução/FPS divergentes ou preset não MP4', async () => {
    const {state, adapter} = runtime(); adapter.load(job());
    state.width = 720;
    await assert.rejects(adapter.requestExport('C:\\test.epr', 'C:\\out.mp4'), /tamanho e FPS/);
    state.width = 1080; state.fps = 60;
    await assert.rejects(adapter.requestExport('C:\\test.epr', 'C:\\out.mp4'), /tamanho e FPS/);
    state.fps = 30; state.extension = 'mov';
    await assert.rejects(adapter.requestExport('C:\\test.epr', 'C:\\out.mp4'), /não produz MP4/);
    assert.equal(state.calls.length, 0);
});

test('solicitação usa engine do Premiere, sequência inteira e continua sem prova de conclusão', async () => {
    const {state, adapter} = runtime(); adapter.load(job());
    await adapter.requestExport('C:\\test.epr', 'C:\\out.mp4');
    assert.equal(state.calls[0][2], 'HOST_IMMEDIATE');
    assert.equal(state.calls[0][5], true);
    const receipt = adapter.report();
    assert.equal(receipt.state, 'experimental');
    assert.equal(receipt.exportProven, false);
    assert.equal(receipt.observations.at(-1).exportCompleted, false);
    assert.ok(!JSON.stringify(receipt).includes('C:\\'));
});

test('recusa exportação não aceita pelo host', async () => {
    const {state, adapter} = runtime(); adapter.load(job()); state.exportAccepted = false;
    await assert.rejects(adapter.requestExport('C:\\test.epr', 'C:\\out.mp4'), /não confirmou/);
    assert.equal(adapter.report().observations.length, 1);
});

test('observações retornadas não permitem reescrever estado interno', async () => {
    const {adapter} = runtime(); adapter.load(job());
    const report = adapter.report(); report.observations[0].state = 'comprovadamente_funcional';
    assert.equal(adapter.report().observations[0].state, 'experimental');
});
