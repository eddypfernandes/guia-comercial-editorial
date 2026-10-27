# Protótipo do ciclo editorial

Este protótipo valida a configuração e seleciona pautas previamente fornecidas em JSON. **Ainda não pesquisa a internet, não usa Gemini, não confirma a veracidade das fontes e não publica conteúdo.**

## Requisitos

Python 3.11 ou superior. O protótipo usa apenas a biblioteca padrão do Python.

## Validar a configuração

Na raiz do repositório:

```bash
python prototipo/validar_config.py
```

## Preparar um ciclo de teste

1. Copie `prototipo/entrada/pautas.exemplo.json` para `prototipo/entrada/pautas.json`.
2. Substitua o exemplo por pautas reais coletadas e verificadas manualmente. Não use o exemplo como notícia factual.
3. Execute:

```bash
python prototipo/ciclo_editorial.py
```

4. Consulte `prototipo/saida/relatorio-ciclo.json`.

O seletor respeita a validade informada, rejeita entradas inválidas, reduz duplicidades de ID, URL e título e limita a seleção a duas pautas por pilar. A pontuação é um critério de ordenação, não uma prova de qualidade ou veracidade.

## Testes

```bash
python -m unittest prototipo/testar_prototipo.py -v
```

## Próxima etapa

Integrar uma coleta de fontes permitidas, guardar evidências e datas de consulta, e só então avaliar a integração com Gemini. Credenciais devem ficar em segredos protegidos, nunca nos arquivos versionados.
