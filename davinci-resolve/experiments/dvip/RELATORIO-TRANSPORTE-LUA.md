# Correção do transporte dos relatórios Lua (12/10/2026)

## Erro concreto

O código novo usava `bmd.writestring(path, json)` em `lua_probe.lua` e `lua_edit_smoke.lua` supondo que isso gravaria relatórios. Na API Fusion, `writestring` serializa dados em memória; a função de gravação é `writefile`. O supervisor, consequentemente, podia ficar esperando um JSON que não foi persistido.

A correção substitui essas chamadas por `bmd.writefile(path, json)`, com tratamento explícito de erro, booleano retornado e sem declaração de sucesso caso a escrita falhe. A escolha de texto como segundo argumento é baseada em exemplos públicos de scripts Fusion; permanece necessário verificar o formato real escrito pelo binário 21.1.1 no Linux.

Referências:
- https://zenn.dev/hitsugi_yukana/articles/dvr_create_macro
- https://www.steakunderwater.com/wesuckless/viewtopic.php?start=165&t=1411
- https://github.com/samuelgursky/davinci-resolve-mcp/issues/203

## Verificação sem instalar Resolve

`test_lua_smoke.lua` executa os próprios arquivos Lua em um interpretador Lua 5.1, com uma API Resolve simulada e respostas determinísticas. Verifica projeto, importação, timeline, codec de formato `mov`, submissão de job, relatórios e cenários em que a escrita não está disponível ou retorna false. Além disso o workflow leve executa testes Python e `luac5.1 -p`.

**O teste não prova a capacidade real de escrever em disco na edição gratuita do Resolve.** Há relatos contraditórios sobre restrições de `bmd.writefile` no Linux/Windows 21.1. Se houver sandbox impedindo escrita, registrar a limitação em vez de inventar exportação. Não houve nova execução pesada, alteração de licença, binário proprietário ou download de mídia.
