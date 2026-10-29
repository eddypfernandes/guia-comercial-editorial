# Agente Comercial — GUIA COMERCIAL

## Objetivo

Pesquisar estabelecimentos em fontes públicas adequadas, organizar e validar os dados essenciais, preparar a localização geográfica e gerar registros estruturados para apresentação gratuita no Guia Comercial.

## Escopo inicial

- Território-piloto: Núcleo Bandeirante, Brasília/DF.
- Busca abrangente por múltiplas fontes e categorias.
- Padronização dos dados e identificação de possíveis duplicidades.
- Registro da origem e da data da coleta.
- Coordenadas e estado de validação da localização, quando disponíveis.
- Fotografia somente quando sua origem e condições de uso forem adequadas; caso contrário, a página utiliza um placeholder HTML com Bootstrap.
- Saída em JSON, sem banco de dados nesta primeira fase.
- Preparação para os módulos do site:
  - `/novo/comercial/index.asp`
  - `/novo/comercial/ver.asp`
  - `/novo/includes/home_comercial.asp`

## Princípios

1. A busca pode ser ampla; a organização e a estrutura dos registros devem ser rigorosas.
2. Não inventar nem completar por suposição dados ausentes.
3. Registrar a fonte e a data de coleta.
4. Distinguir dados encontrados, dados validados e registros publicados.
5. Respeitar licenças, termos de uso, limites de acesso e legislação aplicável às fontes.
6. Não conectar este agente ao workflow editorial existente nem alterar seus arquivos ou sua publicação.
7. A base pública gratuita é independente do banco comercial futuro, que só será planejado para a etapa de reivindicação e contratação.

## Estrutura inicial

- `config/territorios.json`: território e estratégia de expansão.
- `data/estabelecimentos.json`: contrato inicial da saída pública; começa vazio.
- Os módulos de coleta, validação, geolocalização, testes e automação serão acrescentados após a escolha das fontes adequadas.

## Estado

Estrutura inicial de planejamento. Nenhuma coleta automática ou publicação comercial está ativada ainda.
