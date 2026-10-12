# Diagnóstico e controle de cota — 12/10/2026

Execução real: https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38188809728
Artefato: https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38188809728/artifacts/11720970457

A tentativa confirmou a janela principal, o contexto OpenCL e GLInterop. Ldd das três bibliotecas principais de Fusion não encontrou dependências ausentes. O backtrace foi coletado e mostra a interface em QCoreApplication::exec e threads Fusion de scripting/socket/eventos carregadas. Uma captura isolada de espera não comprova deadlock. Nenhum script executou: menu No Scripts e SDK sem conexão. Causa de indisponibilidade da integração continua não determinada; nenhuma importação ou render comprovado.

Com apenas 1% restante informado pelo usuário, os dois workflows experimentais que iniciam o Resolve passaram a executar somente por workflow_dispatch. Commits e alterações de código não iniciarão essas tentativas pesadas. Os arquivos e a branch main foram preservados. Nenhum teste pesado foi iniciado para esta mudança.

A alteração controla consumo; não é uma correção comprovada do registro de scripts. Próxima investigação deve focar disponibilidade e registro da integração interna usando a documentação oficial da edição instalada e os artefatos existentes, antes de repetir download ou render.
