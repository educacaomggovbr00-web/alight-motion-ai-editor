const uxp = require('uxp');
const ppro = require('premierepro');
const {createAdapter, AdapterError} = require('./adapter.js');
const fs = uxp.storage.localFileSystem;
const adapter = createAdapter(ppro, uxp.host.version);
const status = document.getElementById('status');
const buttons = ['load', 'inspect', 'import', 'sequence', 'save-project', 'export', 'report'];
let jobId = null;
let busy = false;

function onClick(id, operation) {
    document.getElementById(id).addEventListener('click', async () => {
        if (busy) return;
        busy = true;
        buttons.forEach(b => { document.getElementById(b).disabled = true; });
        try {
            const result = await operation();
            if (result) status.textContent = result;
        } catch (error) {
            // Não copiar mensagens nativas: podem incluir caminhos ou dados privados.
            status.textContent = error instanceof AdapterError ? error.message : 'Etapa bloqueada por erro nativo ou arquivo inválido. Confira os requisitos e o debugger local; mensagens nativas não são incluídas no relatório.';
        } finally {
            busy = false;
            buttons.forEach(b => { document.getElementById(b).disabled = false; });
        }
    });
}
function pathInFolder(folder, name) {
    const base = folder.nativePath.replace(/[\\/]+$/, '');
    return base + (/^[A-Za-z]:|^\\\\/.test(base) ? '\\' : '/') + name;
}

onClick('load', async () => {
    const file = await fs.getFileForOpening({types: ['json']});
    if (!file) return 'Seleção cancelada.';
    const text = await file.read();
    if (text.length > 100000) throw new Error('JSON muito grande');
    const job = adapter.load(JSON.parse(text));
    jobId = job.job_id;
    document.getElementById('job-label').textContent = `${jobId}: ${job.export.width}×${job.export.height}, ${job.export.fps} FPS`;
    return 'Tarefa carregada. Efeitos do estilo ainda não implementados.';
});
onClick('inspect', async () => {
    const count = await adapter.inspect();
    return `Projeto ativo observado; ${count} sequência(s). Confira visualmente a interface.`;
});
onClick('import', async () => {
    const files = await fs.getFileForOpening({allowMultiple: true, types: ['mp4', 'mov', 'wav', 'mp3']});
    if (!files || !files.length) return 'Seleção cancelada.';
    const count = await adapter.importMedia(files);
    return `API aceitou ${count} arquivo(s). Confirme vídeo/áudio no painel Projeto antes de criar a sequência.`;
});
onClick('sequence', async () => {
    await adapter.createSequence();
    return 'Sequência criada a partir da mídia. Confira os clipes e ajuste tamanho/FPS ao formato da tarefa. Música separada e efeitos ainda são manuais.';
});
onClick('save-project', async () => {
    await adapter.saveProject();
    return 'API confirmou salvamento. Confira o .prproj na área privada.';
});
onClick('export', async () => {
    if (!jobId) throw new Error('Tarefa ausente');
    const preset = await fs.getFileForOpening({types: ['epr']});
    if (!preset) return 'Seleção cancelada.';
    const folder = await fs.getFolder();
    if (!folder) return 'Seleção cancelada.';
    const name = `${jobId}-${Date.now()}.mp4`;
    if ((await folder.getEntries()).some(e => e.name === name)) throw new Error('Destino já existe');
    await adapter.requestExport(preset.nativePath, pathInFolder(folder, name));
    return `Solicitação aceita pelo Premiere: ${name}. Aguarde a conclusão na interface, valide com FFprobe e assista ao MP4. Exportação ainda não comprovada.`;
});
onClick('report', async () => {
    const report = adapter.report();
    const folder = await fs.getFolder();
    if (!folder) return 'Seleção cancelada.';
    const file = await folder.createFile(`uxp-${jobId}-${Date.now()}.json`, {overwrite: false});
    await file.write(JSON.stringify(report, null, 2));
    return 'Relatório experimental salvo localmente. Nenhum arquivo ou credencial foi enviado à rede.';
});
