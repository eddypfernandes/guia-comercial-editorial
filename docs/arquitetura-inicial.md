# Arquitetura inicial — Agente Editorial

## Fluxo pretendido

1. Iniciar um ciclo editorial programado ou manual.
2. Pesquisar assuntos nas fontes disponíveis e descobrir fontes adicionais.
3. Avaliar confiabilidade, atualidade, interesse público e pertinência local.
4. Comparar com o histórico para reduzir duplicidades.
5. Apurar fatos e registrar URLs, título da fonte, entidade publicadora e data de consulta.
6. Redigir conteúdo original para um dos cinco pilares.
7. Validar consistência, riscos, atualidade e referências.
8. Gerar uma imagem ilustrativa quando apropriado e identificá-la como criada por IA.
9. Definir validade individual e estado editorial.
10. Salvar o resultado para visualização no protótipo.
11. Em fase futura, integrar com a interface ASP Clássico e publicar somente após habilitação explícita.

## Regra de quantidade

Manter como referência de 1 a 2 conteúdos ativos por pilar. Não criar uma matéria fraca apenas para atingir a quantidade. O histórico mínimo deve sobreviver à expiração para ajudar a evitar repetição.

## Estados editoriais iniciais

- `coletado`
- `em_analise`
- `aprovado`
- `publicado`
- `rejeitado`
- `expirado`
- `retirado`
- `corrigido`

Os estados podem ser simplificados na implementação, desde que a rastreabilidade seja preservada.

## Separação de dados

**Metadados**: título, resumo, pilar, datas, estado, validade, fontes, identificador da imagem e histórico de alterações.

**Arquivos**: imagem gerada e eventuais versões de pré-visualização. Os arquivos não devem ser confundidos com os registros que descrevem esses arquivos.

## Segurança

- Segredos fora do código e do histórico Git.
- Nenhuma publicação oficial durante o protótipo.
- Nenhuma alteração nos repositórios de automações existentes.
- Respeitar termos de uso, limites de acesso e políticas das fontes consultadas.
- Conteúdos de saúde, veterinária e exercício precisam de validação reforçada.

## Orquestração

O GitHub Actions poderá executar tarefas agendadas ou manuais. O agendamento automático só deve ser ativado depois de existir uma execução segura, com limites de custo, logs e tratamento de falhas. Actions não é armazenamento persistente; resultados duradouros devem ser guardados em local apropriado.

## Persistência

Ainda não se escolheu entre Access, MySQL ou outro mecanismo. A decisão deve ser tomada depois de definir o formato e volume dos registros e verificar como o protótipo será executado. Não migrar nem alterar a base existente sem autorização específica.
