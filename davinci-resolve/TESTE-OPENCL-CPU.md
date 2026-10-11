# Teste executado: OpenCL por CPU

A pedido do usuário, foi feito teste real de processamento por software, sem GPU física. Pacotes Debian oficiais PoCL 6.0-6, LLVM/Clang 18.1.8 e clinfo foram baixados e extraídos em pasta privada, sem alterar o sistema. Nenhum recurso pago foi contratado.

`clinfo` encontrou plataforma Portable Computing Language e dispositivo `cpu-skylake-avx512-AMD EPYC 9V74 80-Core Processor`. O programa C compilou um kernel OpenCL, enviou valores [1,2,3,4], executou v*2+1 e leu [3,5,7,9], conferindo cada resultado. Tipo de dispositivo OpenCL=2 (CPU). Dois workers e prazo máximo 45 segundos. O cache e kernels ficaram fora do repositório.

Resultado: **OpenCL CPU testado e funcional para este kernel**. Não é benchmark de vídeo nem prova de compatibilidade Resolve. Não foi falsificado tipo de dispositivo, criada VRAM dedicada ou emulada GPU NVIDIA. A versão gratuita do Resolve não foi instalada/aberta: nenhum instalador oficial está disponível no ambiente. Não houve transcrição/exportação pelo Resolve.

Reproduzir no Linux com PoCL, GCC e loader OpenCL instalados:

```bash
gcc -O2 davinci-resolve/opencl_cpu_probe.c -Wl,-l:libOpenCL.so.1 -o /tmp/opencl_cpu_probe
POCL_MAX_PTHREAD_COUNT=2 timeout 45 /tmp/opencl_cpu_probe
```

Workflow separado `testar-davinci-opencl-cpu.yml` executa o mesmo cálculo real no Actions e publica somente JSON. Não inicia Resolve nem Windows. O programa usa a primeira plataforma disponível e solicita um dispositivo CPU; a máquina testada não tem GPU exposta. O executável encerra após conferir resultado; recursos OpenCL são liberados pelo processo ao encerrar.

Para testar o aplicativo real, o próximo item ausente é um instalador Linux obtido do [download oficial Blackmagic](https://www.blackmagicdesign.com/event/davinciresolvedownload). O formulário solicita dados pessoais: não foram preenchidos dados inventados e não se pede senha. Quando o instalador estiver disponível privadamente, será possível tentar instalação/abertura experimental com sessão gráfica apropriada e registrar erro ou sucesso. PoCL não garante que o Resolve aceite dispositivo CPU. Os requisitos da versão, dependências e licença continuam aplicáveis. A emulação Windows/WARP anterior é outro teste e não comprova compatibilidade Resolve.
