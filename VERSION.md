# Changelog

Todas as mudanças notáveis neste projeto são documentadas neste arquivo.

O formato é baseado em [Versionamento Semântico (SemVer)](https://semver.org/lang/pt-BR/).

---

## [2.0.4] - 2026-04-29

### [Adicionado]
- **Interface de Sincronização Unificada**: Novo diálogo centralizado (`open_cad_auth_dialog`) que integra credenciais CAD, seleção de relatórios (NEAC/CAD) e monitoramento de progresso em tempo real.
- **Diagnóstico Profundo**: Sistema de log aprimorado em `coleta_cad_consolidada.py` que captura o estado do navegador e o HTML da página em caso de falha crítica nos downloads.

### [Alterado]
- **Gestão de Estado da UI**: Implementação de `st.empty()` e lógica de containers exclusivos para garantir que a tela de seleção seja completamente removida após o início da coleta, eliminando sobreposições.
- **Robô de Coleta CAD (Resiliência)**:
  - **Descoberta Inteligente**: O robô agora busca o botão de download por múltiplos padrões (`Baixar`, `DOWNLOAD`, seletores CSS e links diretos `.xls`).
  - **Tratamento de Janelas**: Melhora na detecção de abas de exportação do ScriptCase, com fallback automático para varredura de páginas abertas se o evento de `page` falhar.
  - **Normalização Unicode**: Comparação de nomes de relatórios agora utiliza normalização `NFD` para evitar erros de casamento de nomes devido a acentos ou codificações distintas.

### [Corrigido]
- **Duplicidade de Botões**: Remoção de lógica redundante na barra lateral que causava a exibição de botões extras durante a sincronização.
- **Falha de Download CAD**: Corrigido o problema onde o robô não conseguia localizar o link de download final após o processamento do relatório.

---

## [2.0.3] - 2026-04-22

### [Adicionado]
- **Componente `_render_kpi_card()`:** Novo componente HTML/CSS premium que substitui todos os `st.metric()` e a função legada `box_html()`. Características:
  - Tipografia **Inter** com label em cinza (`#6B7280`), valor em bold (`700`) e sublabel separado por linha fina.
  - Ícone **Material Symbols Rounded** no canto superior direito com opacidade discreta.
  - Borda lateral esquerda colorida (`4px`) por categoria semântica (vermelho, azul, âmbar, verde, violeta).
  - Sombra suave (`box-shadow`) em substituição a bordas sólidas.
  - Efeito hover com elevação (`translateY(-3px)`) e sombra aprofundada.
  - Altura fixa (`130px`) garantindo alinhamento uniforme entre cards com e sem sublabel.

### [Alterado]
- **Inversão de Fluxo visual (Tabela Primeiro):** Reordenação do layout nas abas **Analítico**, **Consolidado** e **Comparativo**. Agora as tabelas, gráficos e KPIs são exibidos no topo da página, com os filtros e configurações de período movidos para a parte inferior (em expanders recolhidos por padrão), otimizando o foco nos resultados.
- **Aba Início:** Substituição da função `box_html()` e suas classes CSS customizadas pelos novos `_render_kpi_card()`, com sublabels de delta comparativo (↑/↓ vs mês anterior) e lógica de cor contextual (vermelho para crimes, verde para operacional).
- **Estilo de Tabelas (Geral):** Refatoração da função `_apply_table_style()` com foco em escaneabilidade e estética premium:
  - **Tratamento de ruído:** Valores nulos ou zeros substituídos pelo traço "—".
  - **Alinhamento:** Textos à esquerda e dados numéricos à direita (padrão ouro financeiro).
  - **Legibilidade:** Implementação de *Zebra Stripes* (linhas alternadas) e negrito na coluna TOTAL.
  - **Acabamento:** Arredondamento dos cantos (`border-radius`) da linha de TOTAL GERAL (azul PMAL) para consistência com o estilo dos cards.
- **Ícones de subtítulos:** Migração global do `@import` da fonte `Material Symbols Rounded` da função `render_home_dashboard` para o bloco CSS raiz (`<style>` global), garantindo disponibilidade em todas as abas sem recarregamento.
- **Uniformização visual:** Todas as abas (MVI, Analítico MVI, CVP/Patrimônio, Drogas e Início) utilizam agora o mesmo padrão de card de KPI e estilização de tabelas.

---

## [2.0.2] - 2026-04-22

### [Alterado]
- **Otimização da Barra de Navegação:** Unificação do seletor de Ano de Referência e do botão Sincronizar na mesma linha horizontal que as abas de fluxo (1 única linha composta por 8 itens), mitigando o desperdício de espaço vertical no cabeçalho.
- **Visualização Gráfica:** Conversão de todos os gráficos em linha referentes à "Evolução Mensal" (`px.line`) para o formato de barra vertical analítica (`px.bar`), ostentando os dados numéricos de ocorrência projetados dinamicamente no topo de cada correspondência do eixo temporal.
- **Hierarquia de Dados de Fluxo:** Reversão profunda de layout nas abas principais ("Consolidado/Operacional MVI", "Analítico MVI" e "Patrimônio/CVP") a fim de renderizar inicialmente as Listagens Nominais e/ou Matrizes quantitativas antes das suas contrapartes gráficas de visualização de performance.
- **Iconografia Embutida:** Fixação tipográfica de Material Design contornando o Markdown Parsing; agora o campo do "Painel de Indicadores" no cabeçalho integra o ícone através de injeção pura de tag e `fonts.googleapis`.

---

## [2.0.1] - 2026-04-22

### [Alterado]
- Organização completa do projeto em subpastas seguindo boas práticas de arquitetura:
  - `assets/`: imagens e logos do dashboard.
  - `logs/`: arquivos de log de automação, relatórios HTML e imagens de depuração.
  - `testes/`: scripts de depuração, mapeamento, exploração e testes manuais da interface do Pentaho/CAD.
  - `coleta/`: scripts unificados de extração automática dos dados.
- Interface popup de credenciais do CAD atualizada de janelas cinzas padrão (simpledialog) para design moderno Dark Mode (janela customizada flat, centralizada, sem título com botões hover).
- Caminhos do arquivo `app.py`, `Iniciar_Coleta.bat` e scripts filhos atualizados para refletir a nova disposição dos diretórios.

---

## [2.0.0] - 2026-04-15

### [Adicionado]
- Integração do botão **Sincronizar Bancos** diretamente no cabeçalho da página principal (ao lado do seletor de ano), dispensando o uso da sidebar para esta função.
- Seletor de **Ano de Referência** movido da sidebar para a linha de navegação, junto ao botão Sincronizar.
- Informação **"Fonte de Dados: NEAC / CAD / Pentaho"** adicionada ao cabeçalho, acima de "Created By", com tipografia padronizada e mesma espessura de fonte.
- **Sistema de ícones Material Design** (`st.button(icon=":material/...")`) aplicado a todos os botões de navegação e indicadores:
  - Navegação principal: Início, Consolidado, Comparativo, Crimes Vida, Patrimônio, Operacional.
  - Sub-navegação Consolidado: Relatório Anual, Análise Mensal / Cidade.
  - Sub-navegação Comparativo: Comparativo Anual, Análise Temporal Personalizada.
  - Indicadores de Crimes Vida e Operacional.
  - Botão Sincronizar.

### [Alterado]
- **Navegação principal** migrada de `st.tabs()` para botões com `st.session_state`, padrão 100% consistente com os menus internos. Botão ativo exibe marcador `✓`.
- **Abas de Indicadores** (Operacional e Crimes Vida) padronizados com ícones Material e remoção de emojis Unicode antigos.
- **Cabeçalho (Header):** efeito **Glassmorphism** (`backdrop-filter: blur(10px)` + gradiente com transparência). Brasões com fundo branco sólido e sombra para maior contraste.
- **Título "Dashboard Estatístico"** com `font-weight: 900` (Ultra Bold) para hierarquia visual clara.
- **Estilo das Tabs** migrado para modelo corporativo minimalista: fundo transparente, separador inferior (`border-bottom`), sem caixas arredondadas.
- **Gutter System** aprimorado: maior espaçamento entre seções (`margin-bottom: 28px`, `padding-top: 2rem`, `hr: 28px`, `h2/h3` com margens ajustadas).
- **Micro-interações** nos botões: `transform: translateY(-3px)` e sombra elevada no hover, com transição suave de `0.2s`.
- Coleta de dados do **CAD** configurada para modo **headless** (`headless=True`), eliminando janela visível do navegador durante a sincronização.
- Seção "FONTES DE DADOS" removida da sidebar; sidebar simplificada (logo, municípios e versão).
- **"Fonte de Dados"** e **"Created By"** no header trocados de posição e padronizados com mesma fonte e tamanho.

### [Corrigido]
- Conteúdo da página ficava recuado ao posicionar botão Sincronizar dentro de colunas junto às abas. Corrigido mantendo tabs fora de colunas e botão em coluna independente.

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
