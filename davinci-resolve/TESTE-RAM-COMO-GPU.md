# Teste da ideia: reservar RAM como disco e buffer gráfico

11/10/2026, ambiente Codex. Não foi um teste no GitHub Actions.

## O que foi realmente feito

1. Criada uma imagem de disco de **128 MiB** no tmpfs /dev/shm, escrevendo todos os bytes para reservar memória real (não apenas criar um arquivo esparso).
2. Formatada como FAT16; arquivo sintético PROVA.TXT gravado e lido com mtools. Conteúdo e SHA-256 conferidos.
3. Alocado um buffer de **64 MiB pela API OpenCL real** do Rusticl/Zink/Lavapipe. Todos os bytes preenchidos; primeira e última palavras lidas corretamente como 0x12345678.
4. Imagem FAT16 e buffer OpenCL mantidos ativos enquanto o executável original DaVinci Resolve 21.1.1 foi aberto por 30 segundos.
5. Captura e logs salvos; processos encerrados e imagem temporária em RAM removida. Uso do tmpfs retornou a zero.

## Resultados

| Teste | Resultado |
| --- | --- |
| Imagem FAT16 em RAM | Leitura e gravação passaram |
| Buffer de computação OpenCL em RAM | Reserva, preenchimento e leitura passaram |
| Surgimento de GPU física | Nenhuma |
| Executável original iniciado | Sim |
| Inicialização DVIP | Falhou |
| Edição ou exportação | Não comprovadas / não iniciadas |

A imagem é um disco virtual em RAM, não um pendrive USB físico e não foi montada como dispositivo de bloco.
O buffer gráfico pertence ao processo de teste; **não foi atribuído como VRAM do DaVinci**. Não foi encontrada uma interface legítima do aplicativo que permita apontar para esse buffer.
O driver por software já utiliza a RAM compartilhada e executa cálculos na CPU; reservar mais RAM não implementou o compartilhamento OpenGL/OpenCL que falhou nos testes anteriores.

Log real:
```text
Unknown zink Vulkan 1.4(llvmpipe (LLVM 19.1.7, 256 bits) (MESA_LLVMPIPE))
Selected compute API: OpenCL
DVIP Exception: OpenCL Context Manager failed to create context.
Failed to initialize OpenCL board manager
```

## Medidas

- Imagem: 134.217.728 bytes de tamanho e de blocos efetivamente alocados.
- Buffer: 67.108.864 bytes; valores lidos: [305419896,305419896].
- MemAvailable antes: 9.675.390.976 bytes.
- Após imagem: 9.535.590.400 bytes.
- Com ambas as reservas: 9.424.601.088 bytes.
- As medidas de memória total também variam com caches e outros processos; a diferença não deve ser tratada como quantidade exata de VRAM criada.
- SHA-256 do conteúdo restaurado: 4f2515aa07c7aef6883f64799b254ac334a37c61a7d9fca9619b0426ce2c98c9.

## Arquivos de reprodução e evidências

- reserve-opencl.py: reserva real, preenchimento, leitura e liberação do buffer; aguarda um byte em stdin para manter a reserva ativa.
- teste-ram-workspace.py: procedimento completo executado, com caminhos específicos para os prefixos privados preparados nesta sessão. Não baixa o Resolve e não instala outro sistema.
- resultado JSON: resultado-ram.json.
- Captura local: /workspace/ram-idea-private/resolve-with-ram.png.

A reprodução requer os prefixos Mesa 26.1.6, LLVM/libclc 19, PRoot, Xvfb, dosfstools e mtools preparados neste ambiente, mais o Resolve original extraído privadamente. Os caminhos devem ser adaptados em outro host. O teste recusa sobrescrever sua imagem e verifica uma margem de memória antes de alocar.

**Conclusão limitada ao teste:** RAM pode funcionar como armazenamento virtual e como memória de computação gráfica. Ambas as reservas funcionaram. Elas não tornaram essa implementação de GPU por software compatível com o motor do DaVinci. Nenhum custo ou alteração de licença; projetos antigos preservados.
