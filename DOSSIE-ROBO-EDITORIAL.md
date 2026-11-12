# Dossiê do robô editorial — Guia Comercial

Última atualização: 12 de novembro de 2026

Este é o registro técnico contínuo do robô editorial. A partir desta versão, cada alteração aplicada ao código, ao workflow ou ao processo de geração do feed deve ser documentada aqui, com seu efeito e a validação realmente executada.

## Estado atual confirmado

- O robô existente continua executando o ciclo editorial no workflow `.github/workflows/prototipo.yml`: valida configuração, executa testes, coleta sugestões, verifica fontes, gera matérias, resume os corpos e atualiza o feed da prévia.
- O feed consumido pela prévia está em `docs/data/materias-editoriais.json`. O arquivo de geração local é `prototipo/saida/materias-editoriais.json`.
- A publicação oficial permanece desativada.
- Na execução #239 do workflow, o feed foi atualizado e conferido: havia 14 matérias, todas com até 440 palavras no campo `corpo`; o maior texto tinha 413 palavras. A matéria mais recente de Heleno passou a ter 208 palavras.

## Comportamento do resumo

O estágio está em `prototipo/resumir_materias.py` e é executado antes da cópia do feed para `docs/data/`.

- Limita o campo `corpo` a 440 palavras e preserva os parágrafos existentes.
- Mantém frases completas em sequência contínua e na ordem de origem. Se ultrapassar 440 palavras, encerra antes da próxima frase completa; só corta uma frase se ela, sozinha, passar do limite. O processo não usa serviço externo nem reescrita generativa.
- Remove ruídos de navegação e chamadas de página, incluindo `Não chegou ainda?` e `Leia no Poder360`, sem descartar o parágrafo factual ao redor.
- Se uma frase isolada exceder o limite, aplica o limite na fronteira de uma palavra e acrescenta reticências.
- A geração remove repetições consecutivas exatas do título, mesmo com diferença de caixa ou acentos. Preserva o esquema do feed e não substitui título, subtítulo ou campos do carrossel por um resumo do corpo.
- O aviso informa que o resumidor não faz reescrita por IA nem checagem factual independente. A verificação de fontes é uma etapa separada do workflow.

## Fluxo de dados

1. O workflow valida a configuração e executa os testes automatizados.
2. Coleta sugestões das fontes configuradas e verifica tecnicamente as fontes originais.
3. Gera ou atualiza as matérias editoriais em `prototipo/saida/materias-editoriais.json`.
4. Resume o corpo de cada matéria presente no feed gerado.
5. Copia o feed para `docs/data/materias-editoriais.json` e versiona as saídas previstas pelo próprio workflow.

## Histórico de alterações

### 2026-11-12 — Resumos coerentes de até 440 palavras e correção de título duplicado

**Motivo:** o teto anterior de 120 palavras deixou pouco contexto e permitiu que uma chamada de página, “Não chegou ainda?”, encerrasse a matéria. O título da matéria de Heleno também chegou duplicado.

**Arquivos:** `prototipo/resumir_materias.py`, `prototipo/testar_resumidor.py`, `prototipo/gerar_materias.py`, `prototipo/testar_materias.py` e `docs/data/materias-editoriais.json`.

**Resultado:** o limite subiu para 440 palavras; o resumidor preserva parágrafos e seleciona um trecho contínuo na ordem do texto, em vez de ranquear frases isoladas. Foram ampliados os filtros de ruído editorial e a limpeza de títulos repetidos. A matéria de Heleno foi corrigida no feed: título e chamada sem duplicação, subtítulo sem chamada promocional e corpo revisado com a cronologia e o diagnóstico em contexto. O corpo tem 208 palavras. O esquema do feed foi mantido.

**Validação:** os testes automatizados do workflow passaram na [execução #239](https://github.com/eddypfernandes/guia-comercial-editorial/actions/runs/43200206655). Os cinco testes do resumidor verificam o teto de 440, preservação dos parágrafos, remoção da pergunta de navegação, continuidade e corte no limite. No IIS local, `/editorial/index.asp` e `/editorial/ler.asp?id=materia-ad3ebb6c9ded` responderam HTTP 200; o título e o corpo corrigidos apareceram e a chamada antiga não apareceu.

**Referências:** [commit do código e da correção da matéria](https://github.com/eddypfernandes/guia-comercial-editorial/commit/87df4187d99e9ca8480b2954469c6e3eca91cee4) · [commit automático do feed e histórico](https://github.com/eddypfernandes/guia-comercial-editorial/commit/55f43c1a4aa2a8ab7a9ff56d1c47d38b3595433e).

### 2026-11-12 — Resumos de até 120 palavras

**Motivo:** adequar o texto de leitura das matérias a um tamanho previsível, sem alterar título, subtítulo ou contrato usado pelo feed e pelo carrossel.

**Arquivos de código:** `prototipo/resumir_materias.py` e `prototipo/testar_resumidor.py`.

**Resultado:** substituído o limite anterior de linhas aproximadas por 120 palavras; resumos organizados em até três parágrafos; incluído teste para uma frase que ultrapassa sozinha o limite. O workflow reprocessou o feed existente. A verificação posterior confirmou 14 matérias, todas com até 120 palavras no corpo.

**Validação:** os cinco testes específicos do resumidor passaram localmente. A suíte local completa não pôde iniciar no Windows porque o Python instalado não tinha `tzdata`; o workflow do GitHub executou a suíte completa e concluiu com sucesso na [execução #238](https://github.com/eddypfernandes/guia-comercial-editorial/actions/runs/43195999070).

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