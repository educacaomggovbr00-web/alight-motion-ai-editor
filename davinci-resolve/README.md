# Atualização: erro do teste corrigido

**O compartilhamento GL/OpenCL por CPU passou em quatro configurações com o Mesa experimental. [Provas e próximo teste DVIP](ERRO-GL-SHARING-CORRIGIDO.md). O DaVinci ainda não foi comprovado nessa configuração.**

# DaVinci Resolve — alternativa preservada no GitHub

Estado: **bloqueado neste ambiente**. Não houve instalação, aplicativo aberto ou exportação pelo Resolve. Não há GPU exposta; o host é Debian 13 x86_64, com aproximadamente 9.7 GiB RAM total. Nenhum recurso pago criado. Os outros editores e workflows continuam preservados.

## Downloads legítimos

[Produto e versão gratuita](https://www.blackmagicdesign.com/products/davinciresolve/) · [Download oficial](https://www.blackmagicdesign.com/event/davinciresolvedownload) · [Suporte e notas de versão](https://www.blackmagicdesign.com/support/family/davinci-resolve-and-fusion).

A página atual anuncia Resolve 21 e fornece formulário de dados pessoais para baixar Windows/Linux. Não preenchemos dados falsos nem expomos cadastro em logs. Escolher **DaVinci Resolve**, não Studio, para a edição gratuita. O aplicativo gratuito não fornece uma máquina GPU gratuita. O download desktop não instala no Android.

A página de download lista Rocky Linux 8.6/CentOS 7.3 para Linux, mas é genérica; confira as notas específicas da versão escolhida antes de instalar. Não tratamos requisitos de versões antigas como prova dos requisitos da 21. GPU, driver, CUDA/OpenCL, RAM, codecs e sessão gráfica precisam de validação na máquina real.

## Diagnóstico reproduzível

```bash
python3 davinci-resolve/preflight.py --output /privado/resolve-host.json
python3 -m unittest discover -s davinci-resolve/tests -v
```

O workflow **DaVinci Resolve — diagnostico, nao renderiza** roda os testes e inspeciona um runner Linux padrão. Abrir pelo Moto G22 em Actions; artefato `davinci-host-diagnostic`. Workflow concluído significa diagnóstico produzido, mesmo que o JSON esteja `bloqueado`. Não significa DaVinci funcional. Nenhum vídeo pessoal ou instalador é publicado.

Este preflight não certifica compatibilidade: GPU exposta/executável existente não provam app iniciado, VRAM suficiente, geração de GPU/driver, sessão remota ou exportação. Não força instalação nem ignora requisitos. O CI não contrata GPU ou instala Resolve.

## Próximo ambiente

O caminho oficial continua sendo uma máquina Windows/Linux compatível cedida gratuitamente, com GPU/driver suportados, armazenamento persistente e acesso remoto autenticado pelo Android. O experimento por CPU agora passou a troca de buffer GL/CL e permite investigar DVIP; isso ainda não certifica o editor. Nenhum host completo de edição foi configurado. Os runners padrão sem GPU não são uma workstation Resolve comprovada. Não foi instalado software para fingir GPU física.

Depois: baixar gratuitamente pelo formulário oficial, instalar na máquina compatível, abrir manualmente, importar um vídeo sintético, criar timeline, exportar e validar com FFprobe. Só então preparar automação com os documentos de scripting incluídos na versão instalada. Não presumir que APIs externas/execução sem interface estão disponíveis na edição gratuita.

No Linux, o suporte H.264/AAC varia por versão/edição: consultar tabela oficial de codecs. Transcodificação auxiliar para DNxHR/PCM pode ajudar a importar, mas FFmpeg não será chamado de render do Resolve. Não criamos APIs, legendas ou presets fictícios.


## Diagnóstico atualizado: DMA-BUF e GL sharing

[Resultados reais de Mesa 26.1.6/26.2.4 e próximos requisitos](TESTE-DMABUF-GL-SHARING.md). DMA-BUF passou; as 16 combinações OpenGL/OpenCL falharam. DaVinci ainda bloqueado para edição/exportação.



## Patch experimental do Mesa: resultado

[Compilação, correções do executor e evidências da tentativa](experiments/PATCH-SOFTWARE-SHARING.md). A revisão anterior falhou. A revisão atual passou o compartilhamento, mas ainda não foi validada no DaVinci.


