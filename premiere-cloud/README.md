# Premiere Pro original na nuvem

Estado: **Windows 11 + dispositivo WARP CPU testados no runner temporário; desktop/Premiere não comprovados.**
Ambiente permanente, GPU compatível e acesso Adobe autorizado continuam ausentes.
[Persistência, backup/restauração e limites com orçamento R$0 no Brasil](reports/persistencia-brasil-orcamento-zero.md).
O GitHub orquestra; a máquina Windows persistente executará o aplicativo Adobe original.
Nenhum preset ou exportação pelo Premiere está comprovado.
Leia o [relatório técnico](reports/2026-10-10.md) antes de gastar ou repetir experimentos.

## Arquitetura implementada e limites

```text
Moto G22 → GitHub Actions privado → runner Windows x64 com label premiere-gpu
                                   ↓
                           área privada de tarefas
                           input / projects / output / reports
                                   ↓ (operação manual inicialmente)
                           Premiere → MP4 → FFprobe → armazenamento privado → Android
```

O workflow `Premiere - preparar tarefa na maquina privada` aceita ID, estilo, intensidade,
30/60 FPS e orientação. Ele diagnostica a máquina e cria `job.json` e pastas persistentes.
Não recebe links privados, não faz upload de mídia, não inicia edição/exportação nem provisiona máquina.
Falha explicitamente neste repositório público. O pipeline completo ainda depende de uma máquina
e do adapter Adobe que será desenvolvido após os testes do aplicativo.

Use um repositório **privado separado** para o runner e para tarefas pessoais. Copie `premiere-cloud/`
e o workflow privado para ele; mantenha este público como código/documentação. Não conecte um runner
persistente com conta Adobe a workflows públicos ou de pull requests não confiáveis.
No privado: Settings → Actions → Runners → New self-hosted runner → Windows x64.
Execute os comandos fornecidos pelo próprio GitHub na sessão gráfica do Windows e adicione o label
`premiere-gpu`. Não instale o runner como serviço: sessão 0 não controla a interface do Premiere.
Configure na máquina `PREMIERE_JOBS_ROOT` para uma área fora do checkout, por exemplo `D:\PremiereJobs`.
Instale Python 3, PowerShell 7 x64 e FFmpeg/FFprobe auxiliares. Reinicie o processo do runner depois
de alterar variáveis. Defina `PREMIERE_WORKER_ENABLED=true` em Settings → Secrets and variables → Actions → Variables
somente após confirmar os requisitos e o acesso. A variável não prova que a máquina existe.
Sem runner online o job pode ficar na fila; o timeout do job limita execução, não espera na fila.
Cancele a execução pelo Android se a máquina estiver desligada. Não há retries ou agenda automática.

## Instalação reproduzível na futura máquina

1. Abra a sessão Windows remota pelo Android. Configure desktop remoto em 1920×1080,
   mantenha sessão ativa e execute PowerShell 7 x64.
2. Rode `./premiere-cloud/windows/preflight.ps1`. Revise `runtime/environment.json` localmente.
   O script aceita somente Windows desktop 11 build >=26100, AVX2 efetivo, RAM >=8 GiB,
   margem de disco >=40 GiB, sessão interativa e NVIDIA/vGPU >=4096 MiB medida por `nvidia-smi`.
   AMD/Intel não são rejeitadas como incompatíveis pela Adobe: estão fora desta primeira sonda automática.
   Exigem inspeção DXGI/driver manual. CPU, geração da GPU, drivers, áudio e display também exigem revisão.
   Não renomeie o Windows Server nem altere flags para simular compatibilidade.
3. Consulte [downloads oficiais Adobe](https://helpx.adobe.com/download-install/apps/download-install-apps/creative-cloud-apps/download-creative-cloud-desktop-app-using-direct-links.html).
   O script `windows/download-creative-cloud.ps1 -Destination D:\AdobeInstall-001` baixa exclusivamente
   o pacote Adobe versionado já documentado, limita tempo/tamanho, inspeciona ZIP e valida assinatura.
   Não segue redirecionamentos. Se o link expirar, atualize somente após consultar a página oficial.
   Não envie esse diretório ao GitHub. A alternativa é baixar pelo navegador Windows na página Adobe.
4. Após revisar preflight e requisitos manuais, rode `windows/start-signed.ps1 -Kind CreativeCloudInstaller
   -Executable 'D:\AdobeInstall-001\extracted\CAMINHO\Set-up.exe'`. Localize o Set-up real no pacote completo;
   não copie somente o EXE sem os arquivos adjacentes. O script verifica assinatura e observa a abertura
   por até 30 segundos, sem matar o aplicativo. Isso não confirma instalação. UAC pode exigir confirmação na sessão.
5. **Login manual obrigatório aqui:** no Creative Cloud aberto na sessão remota, use sua própria conta
   e MFA diretamente na interface Adobe. Não coloque senha/token em chat, Actions, scripts ou logs.
   Confirme licença ou teste válido. Instale Premiere pelo painel Apps e aguarde conclusão visual.
6. Repita preflight: confira executável e ProductVersion. Abra o EXE real com `start-signed.ps1 -Kind Premiere
   -Executable 'C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe'` ajustando o caminho
   à instalação efetiva. Confira Help → About e interface; janela/processo não comprovam uso/licença.
7. Gere uma mídia sintética auxiliar de dois segundos:

   ```powershell
   ffmpeg -v error -f lavfi -i testsrc2=size=1080x1920:rate=30 -f lavfi -i sine=frequency=440:sample_rate=48000 -t 2 -c:v libx264 -pix_fmt yuv420p -c:a aac D:\PremiereJobs\teste\input\video.mp4
   ```

8. No Premiere: crie projeto em `projects`, importe mídia, crie sequência 1080×1920 30 FPS,
   insira vídeo/áudio, altere Scale de 100 para 110 e confirme a imagem. Salve `.prproj`.
   Registre versão, resultado de importação, nome do efeito, duração e horário em relatório **privado**.
9. Exporte **pelo Premiere** para `output/final.mp4`: H.264, 1080×1920, 30 FPS, áudio AAC,
   qualidade alta e bitrate apropriado à fonte. Para 60 FPS use fonte/sequência 60 FPS; horizontal 1920×1080.
   Registre configuração e mensagem de conclusão. Adobe Media Encoder é opcional e precisa instalação separada.
10. Rode `python premiere-cloud/pipeline.py validate --job D:\PremiereJobs\teste\job.json
    --video D:\PremiereJobs\teste\output\final.mp4 --output D:\PremiereJobs\teste\reports\export.json`.
    FFprobe verifica codecs, tamanho, FPS médio, duração positiva e SHA256. Não comprova motor Adobe,
    efeito aplicado, FPS constante nem qualidade visual. Compare duração esperada e assista ao vídeo no Premiere
    e no Android. Não promova estado a funcional apenas por FFprobe.

Em falhas de instalação, consulte [diagnóstico Adobe](https://helpx.adobe.com/creative-cloud/kb/troubleshoot-install-logs-cc.html)
na máquina; mantenha logs brutos privados e publique somente códigos de erro revisados.
O script de abertura preserva a sessão para diagnóstico. Encerrar workflow não encerra necessariamente aplicativos
GUI externos; salve o projeto, feche o editor e desligue a máquina pelo provedor quando terminar.

## Uso no Moto G22

1. No Chrome, entre no GitHub privado; abra Actions → Premiere → Run workflow. Se necessário habilite
   “Site para computador”. Use ID como `edit-001`, escolha estilo/intensidade/formato. Veja resumo e erros na execução.
2. Conecte ao desktop remoto pelo navegador do provedor ou cliente Android oficial. Tela horizontal,
   Wi-Fi estável e modo touchpad ajudam; interface do Premiere será pequena. Zoom do cliente, teclado virtual,
   mouse/teclado Bluetooth são opcionais. O telefone só transmite interface, não renderiza.
3. Envie vídeo e música pelo portal **privado autenticado** do armazenamento escolhido. Na sessão Windows,
   baixe para `input/video.mp4` e `input/music.wav` da tarefa. Nunca use Upload files do repositório público.
   Upload/download privado ainda é manual; não existe portal implementado neste pacote.
4. Analise a música com `pipeline.py analyze --audio CAMINHO --output CAMINHO/events.json --seconds 30`.
   O JSON fornece timestamps aproximados de impactos; ajuste visualmente contra a música antes de editar.
5. Enquanto não houver adapter validado, importe e edite pela interface remota. Os estilos são especificações,
   não efeitos aplicados. Salve projeto, exporte pelo Premiere e valide como acima.
6. Envie `final.mp4` ao armazenamento privado pela sessão Windows e baixe no Chrome Android com login.
   Links temporários, se oferecidos pelo serviço, devem ser curtos e não registrados em Actions/issues.
   Artefatos Actions do repositório público **não são usados para vídeos pessoais**.

## Automação Adobe: próximo teste pequeno

Há agora um **[painel UXP experimental com manifest, interface e adapter](automation/uxp-panel/)**:
carregar tarefa, conferir projeto, importar mídia, criar sequência do clipe selecionado,
salvar e solicitar exportação MP4 pelo próprio Premiere usando um `.epr` real.
O CI testa nove casos de contrato em Node e disponibiliza somente os fontes do painel.
**O painel nunca foi executado no aplicativo Adobe; não comprova instalação ou exportação.**
O workflow Actions ainda prepara tarefas; carregar o painel e os arquivos é uma etapa manual na sessão remota.

UXP está oficialmente disponível a partir do Premiere 25.6. Após verificar a versão instalada,
crie painel pelo [UXP Developer Tool, tutorial Adobe](https://developer.adobe.com/premiere-pro/uxp/plugins/)
na máquina remota e carregue `automation/inspect-active-project.js` no contexto do painel.
O método `Project.getActiveProject()` está na [API oficial](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/classes/project).
Este smoke test verifica somente acesso a um projeto aberto; **não foi executado no Premiere**.
A sonda simples é preservada. O novo painel tem fontes carregáveis no UDT, sem pacote `.ccx`
ou distribuição validada. Não existe executor headless implementado.

O adapter inicial de importação/sequência/salvamento/solicitação de exportação está preparado, mas requer
prova no host real. Próximos passos após isso: alterar uma propriedade/keyframe e validar efeitos/exportação.
Cada operação deverá usar a referência da versão instalada e provar resultado no projeto.
ExtendScript/CEP só após confirmar suporte efetivo dessa versão; QE DOM não é API pública suportada e não é utilizado.
Velocity, interpolação Bezier, motion blur, RGB split e efeitos adicionais continuam pendentes; quando faltar API
pública, executar pela interface ou template criado no Premiere e documentar. Não declarar suporte antes de testar.

## Testes sem Adobe

`python -m unittest discover -s premiere-cloud/tests -v` verifica contrato de tarefa, colisões,
travessia de diretório, symlink, impacto/silêncio e MP4 real sintético validado por FFprobe, incluindo rejeições.
O workflow público CI testa os auxiliares e parseia PowerShell no Windows Server **sem instalar Adobe**.
Os testes de ambiente/Creative Cloud/Premiere/edição/exportação Adobe são separados nos relatórios.
