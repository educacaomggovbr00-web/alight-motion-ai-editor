// EXPERIMENTAL: executar no contexto UXP do Premiere, nunca em Node/terminal.
// API oficial: https://developer.adobe.com/premiere-pro/uxp/ppro-reference/classes/project
async function inspectActiveProject() {
    const ppro = require('premierepro');
    const project = await ppro.Project.getActiveProject();
    if (!project) throw new Error('Abra um projeto de teste no Premiere antes de executar');
    return { state: 'experimental', activeProjectFound: true, exportProven: false };
}
// Integrar ao painel criado pelo UXP Developer Tool; sem comandos fictícios -r/-script.
module.exports = { inspectActiveProject };
