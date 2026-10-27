# Protótipo do ciclo editorial

O fluxo automatizado descobre pautas por RSS, faz triagem opcional com Gemini, tenta extrair texto público das fontes originais e prepara rascunhos opcionais. Nada é publicado.

## Requisitos

Python 3.12 ou superior. O protótipo usa apenas a biblioteca padrão do Python.

## Executar as etapas

\`\`\`bash
python prototipo/validar_config.py
python prototipo/coletar_fontes.py
python prototipo/curar_com_gemini.py
python prototipo/verificar_fontes.py
python prototipo/redigir_rascunhos.py
\`\`\`

Os arquivos gerados ficam em \`prototipo/saida/\`. A triagem e a redação exigem \`GEMINI_API_KEY\`; sem ela, essas etapas são ignoradas. O coletor e a verificação técnica podem funcionar sem Gemini.

## O que cada etapa significa

- \`descoberta-fontes.json\`: sugestões do RSS, ainda não verificadas.
- \`triagem-gemini.json\`: seleção preliminar de até duas pautas por pilar, não uma verificação factual.
- \`fontes-verificadas.json\`: resultado técnico da tentativa de abrir o link e extrair texto da página; páginas bloqueadas ou com texto insuficiente ficam pendentes.
- \`rascunhos-editoriais.json\`: rascunhos originais assistidos por IA com links para fontes e itens que precisam de conferência humana.

A extração não confirma a veracidade das informações. Um rascunho nunca deve ser tratado como pronto para publicação: revise a fonte original, datas, contexto, fatos, direitos de uso e adequação editorial. Não há publicação automática.

## Testes

\`\`\`bash
python -m unittest prototipo/testar_prototipo.py -v
python -m unittest prototipo/testar_coletor.py -v
python -m unittest prototipo/testar_gemini.py -v
python -m unittest prototipo/testar_fontes.py -v
python -m unittest prototipo/testar_rascunhos.py -v
\`\`\`
