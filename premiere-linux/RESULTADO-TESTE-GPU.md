# Resultado da etapa 2 — GPU e Direct3D 11 (2026-10-10)

**Execução:** [GitHub Actions #38083848852](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38083848852)

**Artefato:** [Relatório ZIP (retenção de 7 dias)](https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38083848852/artifacts/11680854550)

## O que passou

- ✅ Instalou Wine 9.0, compilador MinGW-w64 e ferramentas gráficas livres no Ubuntu.
- ✅ Compilou um programa Windows **64-bit** a partir do arquivo aberto windows/d3d11_probe.c.
- ✅ Inicializou a API DXGI no Wine (HRESULT=0x00000000).
- ✅ Conseguiu criar um dispositivo Direct3D 11 (HRESULT=0x00000000, feature level 0xb000 = **11.0**).
- ✅ Gerou logs técnicos para inspeção.

## O bloqueio identificado

- ⚠️ OpenGL expôs **Mesa llvmpipe**, renderização por **CPU**.
- ⚠️ Vulkan expôs deviceType = PHYSICAL_DEVICE_TYPE_CPU e deviceName = llvmpipe.
- ⚠️ O adaptador DXGI emulado pelo Wine anunciou **NVIDIA GeForce GTX 470** e **15988 MiB**. **Esses dados são emulados e NÃO demonstram que o runner tenha essa placa física ou essa VRAM disponível**.
- ⚠️ O Wine registrou uma advertência sobre ausência de wine32, embora os testes de 64 bits tenham completado.

## Conclusão

**O diagnóstico terminou com sucesso, mas NÃO comprova que o Adobe Premiere Pro funciona.**

O Premiere Pro 26.x requer oficialmente **Windows 11 v24H2** e **GPU compatível com pelo menos 4 GB de memória gráfica**, entre outros recursos; o Linux + Wine **não é uma plataforma suportada**. Como o runner usou renderização por CPU, **não recomendamos tentar instalar Premiere ou Creative Cloud nesse servidor como se houvesse compatibilidade comprovada**.

Para testes reais do Premiere original, seria necessário usar uma máquina Windows 11 compatível, com GPU/VRAM apropriadas, instalador legítimo e conta/licença Adobe. No repositório atual, o editor MP4 com FFmpeg segue funcional e é o caminho confiável para automatizar edições.

## Referências

- [Adobe — Requisitos técnicos Premiere 26.x](https://helpx.adobe.com/br/premiere/desktop/get-started/technical-requirements/adobe-premiere-pro-technical-requirements.html)
- [DXVK — Suporte de drivers e Vulkan](https://github.com/doitsujin/dxvk/wiki/Driver-support)
