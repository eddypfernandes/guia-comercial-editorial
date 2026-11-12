# Dossiê do robô editorial — Guia Comercial

Última atualização: 12 de novembro de 2026

Este é o registro técnico contínuo do robô editorial. A partir desta versão, cada alteração aplicada ao código, ao workflow ou ao processo de geração do feed deve ser documentada aqui, com seu efeito e a validação realmente executada.

## Estado atual confirmado

- O robô existente continua executando o ciclo editorial no workflow \`.github/workflows/prototipo.yml\`: valida configuração, executa testes, coleta sugestões, verifica fontes, gera matérias, resume os corpos e atualiza o feed da prévia.
- O feed consumido pela prévia está em \`docs/data/materias-editoriais.json\`. O arquivo de geração local é \`prototipo/saida/materias-editoriais.json\`.
- A publicação oficial permanece desativada.
- Após a atualização do resumidor em 12/11/2026, o workflow processou novamente as matérias do feed. Na verificação do feed publicado nessa execução, havia 14 matérias; todos os 14 campos \`corpo\` estavam no limite de até 120 palavras. O maior resumo tinha exatamente 120 palavras.

## Comportamento do resumo

O estágio está em \`prototipo/resumir_materias.py\` e é executado antes da cópia do feed para \`docs/data/\`.

- Limita o campo \`corpo\` a 120 palavras e até três parágrafos.
- Seleciona frases do texto extraído, usando relevância ao título, frequência de termos e posição. Não usa um serviço externo nem faz reescrita generativa.
- Mantém a ordem original das frases escolhidas e filtra trechos de navegação e publicidade.
- Se uma frase isolada exceder o limite, aplica o limite na fronteira de uma palavra e acrescenta reticências.
- Preserva título, subtítulo, campos do carrossel e o formato do feed. O estágio atualiza \`corpo\`, \`aviso_editorial\` da matéria e o aviso geral do feed.
- O aviso informa que o resumidor não faz reescrita por IA nem checagem factual independente. A verificação de fontes é uma etapa separada do workflow.

## Fluxo de dados

1. O workflow valida a configuração e executa os testes automatizados.
2. Coleta sugestões das fontes configuradas e verifica tecnicamente as fontes originais.
3. Gera ou atualiza as matérias editoriais em \`prototipo/saida/materias-editoriais.json\`.
4. Resume o corpo de cada matéria presente no feed gerado.
5. Copia o feed para \`docs/data/materias-editoriais.json\` e versiona as saídas previstas pelo próprio workflow.

## Histórico de alterações

### 2026-11-12 — Resumos de até 120 palavras

**Motivo:** adequar o texto de leitura das matérias a um tamanho previsível, sem alterar título, subtítulo ou contrato usado pelo feed e pelo carrossel.

**Arquivos de código:** \`prototipo/resumir_materias.py\` e \`prototipo/testar_resumidor.py\`.

**Resultado:** substituído o limite anterior de linhas aproximadas por 120 palavras; resumos organizados em até três parágrafos; incluído teste para uma frase que ultrapassa sozinha o limite. O workflow reprocessou o feed existente. A verificação posterior confirmou 14 matérias, todas com até 120 palavras no corpo.

**Validação:** os cinco testes específicos do resumidor passaram localmente. A suíte local completa não pôde iniciar no Windows porque o Python instalado não tinha \`tzdata\`; o workflow do GitHub executou a suíte completa e concluiu com sucesso na [execução #238](https://github.com/eddypfernandes/guia-comercial-editorial/actions/runs/43195999070).

**Referências:** [commit do código](https://github.com/eddypfernandes/guia-comercial-editorial/commit/3429eae8f32f2f6f7fe57ff74966f72c30b4ea45) · [commit automático do feed](https://github.com/eddypfernandes/guia-comercial-editorial/commit/7a1e39c7e28712af83abfa99c117d9c5975e1885).

## Registro obrigatório das próximas mudanças

Para cada evolução do robô, acrescentar uma entrada datada no início do histórico com:

- motivo e comportamento anterior;
- arquivos e etapas do workflow alterados;
- efeito sobre o feed, os campos e os consumidores;
- testes e verificações executados, com resultado real;
- execução do GitHub Actions e commits relacionados;
- quantidade de matérias processadas e conferência do limite, quando aplicável.

Não registrar tokens, chaves ou outros segredos neste documento.