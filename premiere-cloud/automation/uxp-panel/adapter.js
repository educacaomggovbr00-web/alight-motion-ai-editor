// Implementação original baseada nas assinaturas da API pública Adobe (25.6+).
// Testes Node usam doubles; o runtime real permanece experimental até testar no host.
class AdapterError extends Error {}

const STYLES = ['Anime Shake', 'Velocity Edit', 'AMV Cinematic', 'Glitch Edit',
    'Hard Beat Sync', 'Smooth Zoom', 'Extreme Impact'];

function validateJob(value) {
    if (!value || value.schema_version !== 1 || value.engine !== 'adobe-premiere-pro' ||
        typeof value.job_id !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(value.job_id) ||
        !STYLES.includes(value.style) || !['leve', 'medio', 'forte'].includes(value.intensity)) {
        throw new AdapterError('job.json inválido ou incompatível');
    }
    const exp = value.export;
    if (!exp || ![30, 60].includes(exp.fps) || exp.video_codec !== 'h264' || exp.audio_codec !== 'aac' ||
        !((exp.width === 1080 && exp.height === 1920) || (exp.width === 1920 && exp.height === 1080))) {
        throw new AdapterError('Formato da tarefa inválido');
    }
    // Descartar campos desconhecidos, caminhos, URLs ou eventuais credenciais.
    return {schema_version: 1, engine: value.engine, job_id: value.job_id,
        style: value.style, intensity: value.intensity,
        export: {width: exp.width, height: exp.height, fps: exp.fps, video_codec: 'h264', audio_codec: 'aac'}};
}

function createAdapter(ppro, hostVersion) {
    let job = null;
    let boundProjectPath = null;
    const observations = [];
    function record(operation, details = {}) {
        observations.push({operation, timestampUtc: new Date().toISOString(), state: 'experimental', ...details});
    }
    async function project() {
        if (!job) throw new AdapterError('Carregue job.json primeiro');
        const current = await ppro.Project.getActiveProject();
        if (!current || !current.path) throw new AdapterError('Abra e salve um projeto de teste no Premiere');
        if (boundProjectPath !== null && current.path !== boundProjectPath) {
            throw new AdapterError('O projeto ativo mudou; recarregue a tarefa para vincular este projeto');
        }
        if (boundProjectPath === null) boundProjectPath = current.path;
        return current;
    }
    return {
        load(value) {
            const next = validateJob(value);
            job = next;
            boundProjectPath = null;
            observations.length = 0;
            record('job_loaded');
            return next;
        },
        async inspect() {
            const current = await project();
            const sequences = await current.getSequences();
            record('active_project_observed', {sequenceCount: sequences.length});
            return sequences.length;
        },
        async importMedia(files) {
            if (!Array.isArray(files) || files.length === 0 || files.length > 20 ||
                files.some(f => !f || !f.isFile || typeof f.nativePath !== 'string' || !f.nativePath)) {
                throw new AdapterError('Escolha de 1 a 20 arquivos locais de mídia');
            }
            const current = await project();
            const accepted = await current.importFiles(files.map(f => f.nativePath), false, null, false);
            if (accepted !== true) throw new AdapterError('Premiere não confirmou a importação');
            record('import_api_returned_true', {requestedFileCount: files.length, mediaVisuallyConfirmed: false});
            return files.length;
        },
        async createSequence() {
            const current = await project();
            const selection = await ppro.ProjectUtils.getSelection(current);
            const items = await selection.getItems();
            if (items.length !== 1) throw new AdapterError('Selecione exatamente um clipe de vídeo no painel Projeto');
            const clip = ppro.ClipProjectItem.cast(items[0]);
            if (!clip || await clip.isSequence()) throw new AdapterError('A seleção precisa ser mídia, não sequência');
            if (!await clip.getComponentChain(ppro.Constants.MediaType.VIDEO)) {
                throw new AdapterError('O clipe selecionado não possui vídeo comprovado');
            }
            const sequenceName = 'PC-' + job.job_id;
            const previous = await current.getSequences();
            if (previous.some(s => s.name === sequenceName)) throw new AdapterError('Esta sequência já existe; evite duplicação');
            const created = await current.createSequenceFromMedia(sequenceName, [clip], null);
            if (!created) throw new AdapterError('Premiere não retornou uma sequência');
            if (await current.setActiveSequence(created) !== true) throw new AdapterError('Sequência criada; ativação não confirmada');
            record('sequence_created', {effectsApplied: false, formatConfirmed: false});
            return true;
        },
        async saveProject() {
            const current = await project();
            if (await current.save() !== true) throw new AdapterError('Premiere não confirmou salvamento');
            record('project_save_api_returned_true');
            return true;
        },
        async requestExport(preset, outputPath) {
            if (typeof preset !== 'string' || !/\.epr$/i.test(preset) ||
                typeof outputPath !== 'string' || !/\.mp4$/i.test(outputPath)) {
                throw new AdapterError('Escolha preset .epr e destino .mp4');
            }
            const current = await project();
            const sequence = await current.getActiveSequence();
            if (!sequence || sequence.name !== 'PC-' + job.job_id) {
                throw new AdapterError('Ative a sequência desta tarefa antes de exportar');
            }
            const settings = await sequence.getSettings();
            const rect = await settings.getVideoFrameRect();
            const rate = await settings.getVideoFrameRate();
            if (rect.width !== job.export.width || rect.height !== job.export.height ||
                !rate || !Number.isFinite(rate.value) || Math.abs(rate.value - job.export.fps) > 0.01) {
                throw new AdapterError('Ajuste tamanho e FPS da sequência ao job.json antes de exportar');
            }
            const extension = await ppro.EncoderManager.getExportFileExtension(sequence, preset);
            if (String(extension).replace(/^\./, '').toLowerCase() !== 'mp4') {
                throw new AdapterError('O preset selecionado não produz MP4');
            }
            // IMMEDIATELY usa Premiere; não QUEUE_TO_AME, FFmpeg ou motor alternativo.
            const accepted = await ppro.EncoderManager.getManager().exportSequence(
                sequence, ppro.Constants.ExportType.IMMEDIATELY, outputPath, preset, true);
            if (accepted !== true) throw new AdapterError('Premiere não confirmou a solicitação de exportação');
            record('export_api_returned_true', {requestedEngine: 'adobe-premiere-pro',
                fullSequence: true, exportCompleted: false, ffprobeValidated: false});
            return true;
        },
        report() {
            if (!job) throw new AdapterError('Carregue job.json primeiro');
            return {schema_version: 1, state: 'experimental', job_id: job.job_id,
                hostVersion: String(hostVersion), engine: 'adobe-premiere-pro',
                effectsApplied: false, exportProven: false, observations: observations.map(o => ({...o}))};
        },
    };
}

module.exports = {AdapterError, validateJob, createAdapter};
