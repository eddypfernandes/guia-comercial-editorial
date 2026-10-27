# GUIA COMERCIAL — Agente Editorial

Repositório exclusivo para o protótipo do agente editorial do GUIA COMERCIAL.

## O que já funciona

O GitHub Actions executa a validação, os testes e uma coleta diária de sugestões de pauta via RSS para os cinco pilares: Pet, Lazer, Esportes, Saúde e Fitness.

A coleta está configurada em `config/fontes.json` e usa pesquisas RSS do Google News com foco em Brasília/DF e Brasil. O relatório é produzido em JSON e guardado como artefato do GitHub Actions por 14 dias.

**A coleta é descoberta, não verificação factual.** O sistema registra título, link do agregador, publicação de origem quando identificada, data publicada e horário de consulta. As pautas precisam ser abertas e verificadas na fonte original antes de qualquer redação ou publicação.

## O que ainda não faz

- Não confirma a veracidade das notícias nem lê integralmente todas as matérias.
- Não redige artigos automaticamente.
- Não gera imagens.
- Não integra o Gemini.
- Não publica no site.
- Não altera os outros repositórios do usuário.

## Como executar

Na página [Actions do repositório](https://github.com/eddypfernandes/guia-comercial-editorial/actions), escolha **Ciclo editorial — descoberta de pautas** e clique em **Run workflow** para executar manualmente.

Quando uma execução terminar, abra-a e baixe o artefato **descoberta-editorial**. O workflow também é agendado diariamente às 07h de Brasília (10:00 UTC).

## Testes locais

Requisito: Python 3.11 ou superior, sem dependências externas.

```bash
python prototipo/validar_config.py
python -m unittest prototipo/testar_prototipo.py -v
python -m unittest prototipo/testar_coletor.py -v
```

## Princípios

1. Publicação oficial desativada durante o protótipo.
2. Nenhum fato, citação, negócio local, preço ou horário pode ser inventado.
3. Guardar fontes e datas de consulta.
4. Não preencher metas com conteúdo fraco.
5. Máximo de duas pautas selecionadas por pilar no ciclo de seleção.
6. Tratar validade e duplicidade explicitamente.
7. Manter credenciais fora do código e do histórico Git.
8. Preservar os demais repositórios sem alterações.
