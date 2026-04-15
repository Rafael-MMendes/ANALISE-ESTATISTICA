import pandas as pd

file_path = 'MVI 2025.xls'
try:
    # Ler a planilha pulando as primeiras 8 linhas (0 a 7). A linha 8 tem o cabeçalho.
    df = pd.read_excel(file_path, header=8)
    
    # Limpar linhas vazias baseadas na Data
    df = df.dropna(subset=['Data do Fato', 'Cidade'])
    
    # Filtrar apenas as cidades do 9º BPM
    cidades_9bpm = [
        'Água Branca', 'Canapi', 'Delmiro Gouveia', 'Inhapi', 
        'Mata Grande', 'Olho d Água do Casado', 'Pariconha', 'Piranhas'
    ]
    df = df[df['Cidade'].str.strip().isin(cidades_9bpm)]
    
    # Garantir que a data seja string para conversão
    df['Data do Fato'] = df['Data do Fato'].astype(str)
    
    # Remover linhas que possam ser totalizadores
    df = df[~df['Data do Fato'].str.contains('Total|TOTAL', na=False)]
    
    # Converter para datetime
    df['Data'] = pd.to_datetime(df['Data do Fato'], format='%d/%m/%Y', errors='coerce')
    
    # Filtrar apenas 2025
    df = df[df['Data'].dt.year == 2025]
    
    # Mapear o mês para nome
    meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
    df['Mês'] = df['Data'].dt.month.map(meses_pt)
    df['Mes_Num'] = df['Data'].dt.month
    
    # Agrupar por Cidade e Mês
    resumo = df.groupby(['Cidade', 'Mês', 'Mes_Num']).size().reset_index(name='Quantidade')
    
    # Ordenar para exibição lógica
    resumo = resumo.sort_values(by=['Cidade', 'Mes_Num'])
    
    # Pivotar para colunas de meses
    pivot = resumo.pivot(index='Cidade', columns='Mês', values='Quantidade').fillna(0).astype(int)
    
    # Reordenar as colunas de meses se existirem
    cols_presentes = [meses_pt[m] for m in sorted(resumo['Mes_Num'].unique())]
    pivot = pivot[cols_presentes]
    
    # Adicionar total por cidade
    pivot['Total'] = pivot.sum(axis=1)
    
    # Adicionar total geral na última linha
    pivot.loc['TOTAL GERAL'] = pivot.sum()
    
    # Gerar Markdown
    md = "# Análise de MVI - 9º BPM / AL (2025)\n\n"
    md += "Abaixo está a quantidade de Mortes Violentas Intencionais (MVI) separadas por cidade e mês a mês, referente a 2025.\n\n"
    md += pivot.to_markdown()
    
    with open('analise_mvi.md', 'w', encoding='utf-8') as f:
        f.write(md)
        
    print("Análise concluída com sucesso. Resultados salvos em analise_mvi.md")
    
except Exception as e:
    print(f"Error processing data: {e}")
