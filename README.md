# GUIA COMERCIAL — Agente Editorial

Protótipo do agente editorial do GUIA COMERCIAL, isolado dos demais repositórios.

## O que está automatizado

- Execução diária às 07h de Brasília e acionamento manual pelo GitHub Actions.
- Descoberta de sugestões de pauta por Google News RSS nos pilares Pet, Lazer, Esportes, Saúde e Fitness, com foco em Brasília/DF.
- Testes automatizados da configuração, seleção de pautas, coleta RSS e validação da triagem.
- Triagem preliminar opcional pelo Gemini, limitada aos candidatos coletados, com rejeição de URLs inventadas e máximo de duas sugestões por pilar.
- Relatórios guardados como artefatos do GitHub Actions por 14 dias.

## Gemini

O workflow usa o segredo `GEMINI_API_KEY` e o modelo `gemini-3.6-flash`. Se o segredo não existir, a coleta RSS e os testes continuam funcionando, e a etapa Gemini é ignorada sem falhar. A chave nunca deve ser escrita nos arquivos do repositório.

Para habilitar a triagem: no repositório, abra **Settings → Secrets and variables → Actions → New repository secret**, use o nome `GEMINI_API_KEY` e cole a chave da API do Gemini como valor. Não envie a chave pelo chat. A integração não fica ativa até esse segredo existir.

## Limites importantes

O RSS e a triagem Gemini identificam pistas, não confirmam fatos. A triagem recebe títulos e resumos curtos, não o conteúdo integral das matérias originais. Antes de redigir um artigo, a fonte original deve ser aberta e verificada, especialmente para saúde, veterinária, pets e exercícios.

O protótipo ainda **não** redige artigos completos, gera imagens, publica no site ou altera qualquer outro repositório. A publicação oficial permanece desativada. O conteúdo nunca deve ser inventado para preencher metas.

## Executar manualmente

Abra [Actions](https://github.com/eddypfernandes/guia-comercial-editorial/actions), escolha **Ciclo editorial — descoberta e triagem** e clique em **Run workflow**. Ao terminar, baixe o artefato **descoberta-editorial** e, se o segredo estiver configurado, **triagem-gemini**.

## Testes locais

Requisito: Python 3.12 ou superior, sem dependências externas.

```bash
python prototipo/validar_config.py
python -m unittest prototipo/testar_prototipo.py -v
python -m unittest prototipo/testar_coletor.py -v
python -m unittest prototipo/testar_gemini.py -v
```
