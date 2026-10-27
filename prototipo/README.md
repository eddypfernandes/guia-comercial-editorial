# Protótipo do ciclo editorial

O robô descobre pautas por RSS, faz triagem opcional com Gemini, tenta abrir as páginas originais e extrair texto público e gera matérias editoriais com título, linha fina, corpo e link para a fonte. Nada é publicado automaticamente no site nesta etapa.

## Requisitos

Python 3.12 ou superior. O protótipo usa apenas a biblioteca padrão do Python.

## Executar as etapas

```bash
python prototipo/validar_config.py
python prototipo/coletar_fontes.py
python prototipo/curar_com_gemini.py
python prototipo/verificar_fontes.py
python prototipo/gerar_materias.py
```

Os arquivos gerados ficam em `prototipo/saida/`. A triagem e a redação exigem `GEMINI_API_KEY`; sem ela, a coleta continua funcionando e a geração produz um relatório vazio com o motivo registrado.

## Arquivos de saída

- `descoberta-fontes.json`: sugestões encontradas via RSS.
- `triagem-gemini.json`: seleção preliminar de pautas, quando o Gemini está disponível.
- `fontes-verificadas.json`: tentativa técnica de abrir a página original e extrair texto.
- `materias-editoriais.json`: matérias originais com título, linha fina, corpo e URL exata da fonte. Este é o artefato que será usado para testar a apresentação no HTML.

## Limites importantes

O robô não inventa URLs e descarta respostas sem fonte correspondente ou com campos insuficientes. A extração técnica não confirma a veracidade das afirmações da página; por isso, cada matéria mantém um link para a fonte original e um aviso editorial. O arquivo de matérias é produzido como artefato do GitHub Actions, mas ainda não alimenta o site automaticamente. A publicação no site será uma integração separada.

## Testes

```bash
python -m unittest prototipo/testar_prototipo.py -v
python -m unittest prototipo/testar_coletor.py -v
python -m unittest prototipo/testar_gemini.py -v
python -m unittest prototipo/testar_fontes.py -v
python -m unittest prototipo/testar_materias.py -v
```
