# GUIA COMERCIAL — Agente Editorial

Repositório exclusivo para o protótipo do agente editorial autônomo do GUIA COMERCIAL.

## Objetivo

Preparar, por ciclos, conteúdos úteis e confiáveis para cinco pilares:
- Pet
- Lazer
- Esportes
- Saúde
- Fitness

O agente deverá pesquisar, selecionar pautas, verificar informações, redigir matérias, gerar imagens quando aplicável, registrar fontes e validade, controlar duplicidade e preparar resultados para revisão visual.

## Estado atual

**Protótipo de seleção local implementado; ainda não há coleta automática na internet, integração com Gemini, interface ASP Clássico ou publicação oficial.**

O código atual:
- valida a configuração editorial;
- valida os campos essenciais das pautas de entrada;
- seleciona pautas por pontuação, validade e pilar;
- identifica IDs, URLs e títulos duplicados;
- limita a seleção a duas pautas por pilar sem preencher artificialmente;
- gera relatório JSON para revisão;
- executa testes automatizados no GitHub Actions.

## Como testar localmente

Requisito: Python 3.11 ou superior, sem bibliotecas adicionais.

```bash
python prototipo/validar_config.py
python -m unittest prototipo/testar_prototipo.py -v
```

Para preparar um ciclo, consulte [o guia do protótipo](prototipo/README.md). O arquivo `prototipo/entrada/pautas.exemplo.json` é apenas um modelo estrutural, não uma notícia real.

## Princípios

1. Não publicar automaticamente no site nesta fase.
2. Não inventar fatos, fontes, citações, estabelecimentos ou dados locais.
3. Guardar referências e datas de consulta das fontes usadas.
4. Não produzir conteúdo só para preencher uma vaga.
5. Manter no máximo dois conteúdos ativos por pilar, conforme a regra editorial definida.
6. Expirar ou retirar conteúdo vencido de forma controlada.
7. Manter metadados e arquivos de imagem separados.
8. Não alterar os repositórios `radar-ticker`, `clima` ou `oportunidades`.
9. Manter credenciais fora do código e do histórico Git.

## Próximas etapas

1. Verificar a execução dos testes no GitHub Actions.
2. Integrar coleta de fontes permitidas e registro das evidências.
3. Avaliar integração com Gemini depois de conferir o padrão usado nos repositórios existentes, sem modificá-los.
4. Criar a revisão editorial e a pré-visualização; decidir persistência e interface ASP Clássico numa etapa posterior.
