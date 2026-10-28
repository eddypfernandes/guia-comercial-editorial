# GUIA COMERCIAL — Agente Editorial

Protótipo do agente editorial do GUIA COMERCIAL, isolado dos demais repositórios.

## Ciclo automatizado

- Execução diária às 07h de Brasília e acionamento manual pelo GitHub Actions.
- Descoberta de pautas por Google News RSS nos pilares Pet, Lazer, Esportes, Saúde e Fitness, com foco em Brasília/DF.
- Triagem preliminar opcional pelo Gemini, limitada aos candidatos coletados.
- Tentativa de abrir os links das matérias e extrair texto público da fonte original, com limites de tamanho e bloqueio de URLs locais/privadas.
- Geração opcional de rascunhos editoriais pelo Gemini somente quando há texto extraído suficiente; o verificador analisa uma pauta por pilar por ciclo.
- Testes automatizados para configuração, coleta, triagem, extração e validação de rascunhos.
- Artefatos do GitHub Actions retidos por 14 dias.

## Retenção do conteúdo editorial

- Matérias aptas permanecem ativas por até **72 horas desde a publicação original**, respeitando qualquer prazo menor informado.
- O feed conserva até **20 matérias**, com limite de **4 por pilar**, sempre das mais recentes para as mais antigas.
- Duplicatas e matérias vencidas são removidas na montagem do feed. Se uma coleta não trouxer novidades, as matérias ainda válidas são preservadas.
- Esses limites organizam somente a prévia editorial; a publicação oficial continua desativada.

## Artefatos da execução

No GitHub, abra [Actions](https://github.com/eddypfernandes/guia-comercial-editorial/actions), selecione **Ciclo editorial — descoberta e triagem**, abra uma execução e baixe:
- **descoberta-editorial**: candidatos encontrados por RSS;
- **triagem-gemini**: sugestões preliminares do Gemini, se a chave estiver configurada;
- **fontes-verificadas**: status técnico da resolução dos links e da extração de texto, com amostra de até uma pauta por pilar;
- **rascunhos-editoriais**: até cinco rascunhos produzidos pelo Gemini quando houver chave e fontes elegíveis.

## Ativar o Gemini

O workflow lê o segredo \`GEMINI_API_KEY\` e usa \`GEMINI_MODEL\` (padrão atual no workflow: \`gemini-3.8-flash\`). Para ativar, no repositório abra **Settings → Secrets and variables → Actions → New repository secret**, nomeie como \`GEMINI_API_KEY\` e cole a chave da API. Não coloque a chave no código nem a envie pelo chat.

Sem a chave, o fluxo ainda coleta RSS, tenta extrair páginas e gera relatórios de status, mas não executa triagem por IA nem redige rascunhos.

## Limites editoriais e segurança

Abertura de página e extração de texto são verificações técnicas, **não** confirmação factual. Sites podem bloquear a coleta, depender de JavaScript, exigir assinatura ou fornecer pouco texto; nesses casos, o item permanece pendente de revisão manual. Os rascunhos são sínteses assistidas por IA e podem conter erros mesmo quando citam a fonte correta.

Matérias redigidas pela IA que passam pelas validações automáticas de estrutura, limites editoriais e correspondência com a fonte recebem `status_editorial: "apto_para_publicacao"` e podem seguir para o fluxo editorial do ambiente de teste. Esse status confirma a aprovação pelos critérios automáticos definidos, mas não representa comprovação factual independente. Se a IA estiver indisponível ou a redação não passar nas validações, o sistema gera um rascunho alternativo com revisão obrigatória, que não recebe o status de apto. `publicacao_oficial` permanece `false`: este workflow não publica no site oficial nem modifica outros repositórios. Abertura de página e extração técnica não garantem que todas as afirmações sejam verdadeiras; saúde, veterinária, pets e atividade física exigem cuidado especializado. Não se inventam fatos locais para tornar a pauta relevante.

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
## Contrato visual do carrossel editorial da home

As limitações visuais abaixo se aplicam **somente** ao módulo `/novo/includes/home_editorial.asp`; não devem limitar nem alterar a leitura completa em `/novo/editorial/index.asp`.

- Altura fixa do carrossel: **420 px**.
- Layout desktop: imagem e texto lado a lado, em colunas iguais.
- Layout mobile: imagem acima e conteúdo abaixo.
- Título compacto do carrossel: até **65 caracteres**.
- Linha fina compacta do carrossel: até **140 caracteres**.
- Navegação inferior com setas anterior/próximo, botões circulares contornados e ícones chevron; sem pontos indicadores.
- O agente editorial deve produzir `titulo_carrossel` e `linha_fina_carrossel` concisos, sem alterar os campos `titulo`, `linha_fina` e `corpo` usados na página completa.
- A altura fixa será aplicada ao componente visual; o conteúdo da chamada deve respeitar os limites editoriais para evitar que os slides mudem de altura.

A publicação oficial permanece desativada. As matérias continuam sujeitas a revisão factual e editorial.
