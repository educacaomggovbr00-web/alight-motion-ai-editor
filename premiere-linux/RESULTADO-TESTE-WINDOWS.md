# Resultado da etapa 3 — Windows do GitHub (2026-10-10)

- [Execucao de diagnostico no GitHub Actions](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38084187439)
- [Relatorio original gerado no runner (artefato, retencao 7 dias)](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38084187439/artifacts/11681443734)

## Dados efetivamente obtidos

| Verificacao | Resultado |
|---|---|
| Sistema | Microsoft Windows Server 2025 Datacenter |
| Build | 26100 |
| RAM | 15,99 GiB |
| CPU | AMD EPYC 9V74 (4 processadores logicos alocados) |
| Placa de video | Microsoft Hyper-V Video |
| VRAM fisica | Nao comprovada |
| Premiere Pro.exe no caminho padrao | Nao encontrado |
| Premiere Pro iniciado | Nao |
| Exportacao de video no Premiere | Nao testada |
| Resultado do workflow de diagnostico | Sucesso |

## Conclusao

O diagnostico foi executado corretamente, mas **o Adobe Premiere Pro original nao estava
instalado nem foi iniciado**. O runner Windows utilizado e **Windows Server 2025**,
enquanto a Adobe exige **Windows 11 v24H2** para Premiere 26.x.
O controlador de video reportado e **Hyper-V Video**, sem GPU dedicada
compatível com memoria de video suficiente comprovada.

O teste nao instalou nenhum produto Adobe nem tentou ativacao.
A demonstracao de um comando Wine funcionando num runner Linux
na etapa anterior nao altera essas limitacoes.

**Proximo passo real para testar Premiere:**
uma maquina Windows 11 compativel, GPU com ao menos 4 GiB de memoria grafica
e instalacao/licenca Adobe valida. O GitHub Actions Windows padrao
nao substitui isso. Para editar videos no GitHub com o ambiente atual,
o fluxo FFmpeg do repositorio ja funciona.

Fontes:
- [Adobe Premiere — requisitos tecnicos atuais](https://helpx.adobe.com/br/premiere/desktop/get-started/technical-requirements/adobe-premiere-pro-technical-requirements.html)
- [GitHub Actions — GitHub-hosted runners e opcao de runners com GPU](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners)
