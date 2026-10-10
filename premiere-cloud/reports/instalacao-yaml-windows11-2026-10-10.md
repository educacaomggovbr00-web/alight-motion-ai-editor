# Instalação via YAML e Windows 11

Estado: **bloqueado para instalação; integração preparada, não executada no Premiere**.

Workflow: `.github/workflows/premiere-instalar-windows11.yml`. Não cria VM,
conta Adobe nem licença. Em repositório privado habilitado, usa o runner Windows
X64 `premiere-gpu`, verifica requisitos, baixa Creative Cloud oficial, valida
assinatura Adobe e abre Set-up.exe. Tempo máximo: dez minutos. Não espera o
login nem declara instalação completa. Preserva o aplicativo aberto.

## Etapas pelo celular

1. Obter uma máquina Windows 11 licenciada com GPU compatível (não provisionada;
   recursos pagos precisam de autorização). Preparar acesso remoto pelo Android.
2. Usar cópia privada do projeto. Instalar PowerShell 7 e runner GitHub na sessão
   gráfica do usuário, executando `run.cmd`, não como serviço. Adicionar label
   `premiere-gpu`; configurar `PREMIERE_INSTALL_ROOT` fora do checkout no ambiente
   do runner; definir variável GitHub `PREMIERE_WORKER_ENABLED=true`.
3. No navegador do celular: Actions → Premiere - iniciar instalacao no Windows
   11 privado → Run workflow. Se os requisitos falharem, nada será instalado.
4. Abrir a sessão remota. Concluir Creative Cloud. Escolher criar conta com seu
   próprio e-mail, verificar o e-mail e definir senha diretamente na interface
   Adobe. Não enviar senha ao ChatGPT nem inserir senha ou token no YAML.
5. Com conta e licença/teste autorizado, escolher Premiere no Creative Cloud.
   Depois executar os testes de aplicativo, projeto e exportação descritos no
   README. Uma conta gratuita sozinha não comprova direito de uso do Premiere.

## Ambiente observado

O ambiente desta sessão é Linux. `/dev/kvm` e `/dev/dri` ausentes; nenhum Windows
remoto foi conectado. Não há GPU nem aceleração de VM disponível. Baixar ISO
não transforma esse ambiente em Windows nem comprova GPU ou Premiere instalado.

Microsoft oferece Windows 11 Enterprise de avaliação de 90 dias, não uma edição
oficial chamada “mini”. Não usamos imagens modificadas. O download consultado
é a ISO oficial x64 pt-BR 26H2, tamanho anunciado 8.170.147.840 bytes. A avaliação
não resolve licenciamento permanente ou direitos de desktop em nuvem.

Fontes oficiais:

- https://www.microsoft.com/en-us/evalcenter/download-windows-11-enterprise
- https://support.microsoft.com/en-us/servicing/os/windows/docs/2026/09/verify-the-authenticity-of-a-windows-11-enterprise-evaluation-iso-file

SHA256 publicado para pt-BR:
`29BD7592E832D32073D1637CE83689DE5F375700A963B2D753E437CC64D76C09`.
O resultado da transferência e da comparação deve ser registrado separadamente;
não se deve tratar o tamanho anunciado como download concluído.

## Resultado real

Download **concluído**, 8.170.147.840 bytes, fora do repositório público.
SHA256 calculado igual ao publicado acima. Arquivo privado nesta sessão:
`/workspace/adobe-private-downloads/windows11-enterprise-eval-ptbr.iso`.
Transferência HTTPS do domínio oficial Microsoft, em oito intervalos, seguida de
montagem e verificação SHA256 integral. Nenhum Windows foi instalado/iniciado;
nenhum Premiere foi instalado/iniciado. Esse armazenamento da sessão não é uma
VM persistente nem um serviço de download para o celular.

Testes locais: sete testes Python e nove contratos UXP passaram (sem Adobe).
YAML carregado e restrição de runner verificada. GitHub validou sintaxe dos
scripts PowerShell e repetiu testes auxiliares com sucesso:
https://github.com/educacaomggovbr00-web/alight-motion-ai-editor/actions/runs/38090859947

O workflow de instalação não foi executado em Windows 11: não há runner
compatível conectado e o repositório atual é público. O bloqueio está explícito;
não há evidência de login, conta Adobe criada ou instalação concluída.
