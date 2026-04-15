# Changelog

Todas as mudanças notáveis neste projeto são documentadas neste arquivo.

O formato é baseado em [Versionamento Semântico (SemVer)](https://semver.org/lang/pt-BR/).

---

## [1.1.1] - 2026-04-01

### [Corrigido]
- Botão de recolher sidebar ainda era visível e funcional via CSS puro. Adicionado JavaScript com `MutationObserver` que remove o botão do DOM e impede recriação pelo React do Streamlit.

### [Alterado]
- Largura da sidebar reduzida de `21rem` para `17rem`.

---

## [1.1.0] - 2026-04-01

### [Alterado]
- Menu lateral (sidebar) fixo em estado expandido: removida a funcionalidade de recolher/expandir e bloqueado redimensionamento. Largura fixa de `21rem` com botão de colapso oculto via CSS.

---

## [1.0.1] - 2026-04-01

### [Corrigido]
- Aba **Início** exibia valores zerados por utilizar o mês atual do sistema (Abril) em vez do último mês com dados disponíveis (Março). Agora detecta automaticamente o mês mais recente com dados.
- Aba **Patrimônio** não renderizava conteúdo quando ocorria erro silencioso no carregamento dos dados de CVP. Adicionado tratamento de exceção com mensagem de erro clara.
- Aba **Operacional** apresentava tela em branco em caso de falha no carregamento de qualquer indicador. Adicionado bloco `try/except` com feedback ao usuário.

### [Adicionado]
- Texto informativo na aba **Início** indicando o mês/ano de referência dos dados exibidos e o mês utilizado na comparação de delta.
- Mensagem de aviso específica quando não há arquivo de CVP para o ano selecionado na aba **Patrimônio**.

### [Alterado]
- Lógica de seleção de mês na aba **Início**: agora percorre os meses de Dezembro a Janeiro e exibe o último mês com `soma > 0` nos indicadores, em vez de usar `datetime.now().month`.

---

## [1.0.0] - 2026-03-01

### [Adicionado]
- Dashboard estatístico completo com abas: Início, Consolidado, Comparativo, Crimes Vida, Patrimônio e Operacional.
- Carregamento automático de dados de MVI, CVLI, Tentativa, CVP, TCO, Drogas, Armas, Prisões, Veículos Recuperados, Maria da Penha, Mandados e Visita Comunitária.
- Filtro por ano de referência (2024, 2025, 2026) na barra lateral.
- Exportação de relatórios em formato Excel (XLSX) e PDF com cabeçalho institucional.
- Comparativo ano a ano (YoY) com indicadores semânticos de cor (criminalidade vs produtividade).
- Matrizes de ocorrência por cidade e mês para todos os indicadores.
- Gráficos interativos (barras, linhas, pizza) via Plotly.
- Tema visual institucional 9º BPM / PMAL com CSS customizado.
