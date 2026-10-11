# Resultado real — 11/10/2026

[Execução 38167954887](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38167954887) · implementação `cbb9effb290cc1fb5d3ff2416c1d647af8dbeea1`.

Os 12 testes de segurança, gates, timeout e limites de API passaram no GitHub Actions em 0,106 s. O artefato `davinci-dvip-preflight` contém o relatório e os logs. A execução geral falhou intencionalmente na etapa de bloqueio: **o segredo DAVINCI_RESOLVE_LINUX_URL está ausente**. O job original foi ignorado; não houve compilação nova, download ou início do Resolve.

O sucesso anterior do compartilhamento permanece comprovado. Ainda não existe evidência nova sobre o diálogo Unsupported GPU, a inicialização DVIP, projeto ou exportação. Esses estados permanecem não iniciados ou não comprovados.

A main permanece em `48aaecb8168783c13130833cf23c327349c26471`; nenhum arquivo anterior foi removido. O workflow foi alterado somente na branch experimental. Não há instalador ou link temporário no commit.

Próxima ação necessária: no Android, configurar o segredo privado com um novo endereço oficial Linux 21.1.1. O endereço anterior expirou. Depois abrir Actions → workflow `testar-mesa-software-sharing.yml` → Run workflow → selecionar `experiment/davinci-21-1-1-software-dvip`. Não colocar o endereço em mensagens ou no repositório. O novo teste passa pelos quatro buffers antes de qualquer download e só declara exportação após MP4 real validado.
