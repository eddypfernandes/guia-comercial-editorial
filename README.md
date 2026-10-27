# GUIA COMERCIAL — Agente Editorial

Repositório exclusivo para o protótipo do agente editorial autônomo do GUIA COMERCIAL.

## Objetivo

Produzir, por ciclos, de 1 a 2 conteúdos úteis e confiáveis para cada pilar:
- Pet
- Lazer
- Esportes
- Saúde
- Fitness

O agente deverá pesquisar, selecionar pautas, verificar informações, redigir matérias, gerar imagens quando aplicável, registrar fontes e validade, controlar duplicidade e preparar os resultados para revisão visual.

## Estado atual

**Protótipo inicial — não conectado à hospedagem e sem publicação oficial.**

Nenhuma chave de API deve ser incluída no repositório. Configure credenciais futuramente em GitHub Actions Secrets ou em variáveis de ambiente protegidas.

## Estrutura

- `docs/`: decisões e especificações do projeto.
- `config/`: configuração não secreta do protótipo.
- `prototipo/`: componentes de demonstração.
- `.github/workflows/`: automações do GitHub Actions.
- `.env.example`: nomes ilustrativos de variáveis; não contém credenciais.

## Princípios

1. Não publicar automaticamente no site nesta fase.
2. Não inventar fatos, fontes, citações, estabelecimentos ou dados locais.
3. Guardar referências e datas de consulta das fontes usadas.
4. Não produzir conteúdo só para preencher uma vaga.
5. Manter no máximo dois conteúdos ativos por pilar, conforme a regra editorial definida.
6. Expirar ou retirar conteúdo vencido de forma controlada.
7. Manter metadados e arquivos de imagem separados.
8. Não alterar os repositórios `radar-ticker`, `clima` ou `oportunidades`.

## Próximo desenvolvimento

Implementar primeiro uma execução de teste que produza um relatório de pautas e matérias em artefatos de protótipo, sem publicar no site. A integração com Gemini, persistência e interface ASP Clássico será adicionada em etapas verificáveis.
