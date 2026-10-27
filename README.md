# GUIA COMERCIAL — Agente Editorial

Protótipo do agente editorial do GUIA COMERCIAL, isolado dos demais repositórios.

## Ciclo automatizado

- Execução diária às 07h de Brasília e acionamento manual pelo GitHub Actions.
- Descoberta de pautas por Google News RSS nos pilares Pet, Lazer, Esportes, Saúde e Fitness, com foco em Brasília/DF.
- Triagem preliminar opcional pelo Gemini, limitada aos candidatos coletados.
- Tentativa de abrir os links das matérias e extrair texto público da fonte original, com limites de tamanho e bloqueio de URLs locais/privadas.
- Geração opcional de rascunhos editoriais pelo Gemini somente quando há texto extraído suficiente.
- Testes automatizados para configuração, coleta, triagem, extração e validação de rascunhos.
- Artefatos do GitHub Actions retidos por 14 dias.

## Artefatos da execução

No GitHub, abra [Actions](https://github.com/eddypfernandes/guia-comercial-editorial/actions), selecione **Ciclo editorial — descoberta e triagem**, abra uma execução e baixe:
- **descoberta-editorial**: candidatos encontrados por RSS;
- **triagem-gemini**: sugestões preliminares do Gemini, se a chave estiver configurada;
- **fontes-verificadas**: status técnico da abertura de páginas e texto extraído;
- **rascunhos-editoriais**: rascunhos produzidos pelo Gemini quando houver chave e fontes elegíveis.

## Ativar o Gemini

O workflow lê o segredo \`GEMINI_API_KEY\` e usa \`GEMINI_MODEL\` (padrão atual no workflow: \`gemini-3.6-flash\`). Para ativar, no repositório abra **Settings → Secrets and variables → Actions → New repository secret**, nomeie como \`GEMINI_API_KEY\` e cole a chave da API. Não coloque a chave no código nem a envie pelo chat.

Sem a chave, o fluxo ainda coleta RSS, tenta extrair páginas e gera relatórios de status, mas não executa triagem por IA nem redige rascunhos.

## Limites editoriais e segurança

Abertura de página e extração de texto são verificações técnicas, **não** confirmação factual. Sites podem bloquear a coleta, depender de JavaScript, exigir assinatura ou fornecer pouco texto; nesses casos, o item permanece pendente de revisão manual. Os rascunhos são sínteses assistidas por IA e podem conter erros mesmo quando citam a fonte correta.

Nenhum rascunho é publicação autorizada. Revisão humana deve conferir a fonte original, autoria, data, contexto e todas as afirmações. Saúde, veterinária, pets e atividade física exigem cuidado especializado. Não se inventam fatos locais para tornar a pauta relevante. O workflow não publica no site e não modifica outros repositórios.

## Testes locais

Requisito: Python 3.12 ou superior, sem dependências externas.

\`\`\`bash
python prototipo/validar_config.py
python -m unittest prototipo/testar_prototipo.py -v
python -m unittest prototipo/testar_coletor.py -v
python -m unittest prototipo/testar_gemini.py -v
python -m unittest prototipo/testar_fontes.py -v
python -m unittest prototipo/testar_rascunhos.py -v
\`\`\`
