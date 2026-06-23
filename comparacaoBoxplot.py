import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os

# =====================================================================
# 1. LEITURA E SEPARAÇÃO DOS DADOS (Igual ao outro script)
# =====================================================================
caminho_base = r"Resultados"
padrao_busca = os.path.join(caminho_base, "**", "resultado_completo.csv")
arquivos_csv = glob.glob(padrao_busca, recursive=True)

lista_dfs = []
for arquivo in arquivos_csv:
    df_temp = pd.read_csv(arquivo)
    df_temp['seed_origem'] = os.path.basename(os.path.dirname(arquivo))
    lista_dfs.append(df_temp)

df_completo = pd.concat(lista_dfs, ignore_index=True)

df_uni = df_completo[df_completo['seed_origem'].str.contains('unico', case=False, na=False)].copy()
df_multi = df_completo[df_completo['seed_origem'].str.contains('multi', case=False, na=False)].copy()

# =====================================================================
# 2. LIMPEZA DOS DADOS (Tratamento do erro "nao existe")
# =====================================================================
colunas_de_nota = [
    'nota_antiga', 'nota_nova', 
    'c1', 'c2', 'c3', 'c4', 'c5', 
    'c1_antiga', 'c2_antiga', 'c3_antiga', 'c4_antiga', 'c5_antiga'
]

for col in colunas_de_nota:
    if col in df_uni.columns:
        df_uni[col] = pd.to_numeric(df_uni[col], errors="coerce")
    if col in df_multi.columns:
        df_multi[col] = pd.to_numeric(df_multi[col], errors="coerce")

df_uni = df_uni.dropna(subset=['nota_antiga', 'nota_nova'])
df_multi = df_multi.dropna(subset=['nota_antiga', 'nota_nova'])

# =====================================================================
# 3. PROCESSAMENTO DOS DADOS PARA O BOXPLOT
# =====================================================================
dados_boxplot = []

# Notas Uni-Agente
for i in range(1, 6):
    col_name = f'c{i}'
    temp = df_uni[[col_name]].copy().dropna()
    temp.columns = ['Nota']
    temp['Competencia'] = f'C{i}'
    temp['Modelo'] = 'Uni-Agente'
    dados_boxplot.append(temp)

# Notas Multi-Agente (Agora usa c1, c2 igual o uni)
for i in range(1, 6):
    col_name = f'c{i}'
    temp = df_multi[[col_name]].copy().dropna()
    temp.columns = ['Nota']
    temp['Competencia'] = f'C{i}'
    temp['Modelo'] = 'Multi-Agente'
    dados_boxplot.append(temp)

# Notas Humanas (Ref.) - Pega de qualquer um dos dataframes
for i in range(1, 6):
    col_name = f'c{i}_antiga'
    temp = df_uni[[col_name]].copy().dropna()
    temp.columns = ['Nota']
    temp['Competencia'] = f'C{i}'
    temp['Modelo'] = 'Humano (Ref.)'
    dados_boxplot.append(temp)

df_long = pd.concat(dados_boxplot, ignore_index=True)

# =====================================================================
# 4. GERAÇÃO DO BOXPLOT
# =====================================================================
plt.figure(figsize=(8, 10)) 

sns.boxplot(
    data=df_long,
    y='Competencia', 
    x='Nota',        
    hue='Modelo',
    palette=['skyblue', 'salmon', 'lightgreen'],
    orient='h'       
)

plt.xlabel('Pontuação (0–200)') 
plt.ylabel('Competência')       
plt.grid(True, axis='x', linestyle='--', alpha=0.3) 

plt.legend(title='Avaliador', loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3)

plt.tight_layout() 
plt.savefig('boxplot_comparativo_competencias.png', dpi=300)
plt.close()
print("Gráfico 'boxplot_comparativo_competencias.png' gerado com sucesso!")

# =====================================================================
# 5. TABELA DE FREQUÊNCIA DE NOTAS TOTAIS
# =====================================================================
nota_humano = df_uni['nota_antiga']
nota_uni = df_uni['nota_nova']
# Para o multi, o nome agora também é apenas 'nota_nova'
nota_multi = df_multi['nota_nova']

bins = [0, 200, 400, 500, 600, 700, 800, 900, 1000]
labels = ['0-200', '201-400', '401-500', '501-600', '601-700', '701-800', '801-900', '901-1000']

freq_humano = pd.cut(nota_humano, bins=bins, labels=labels, include_lowest=True).value_counts().sort_index()
freq_uni = pd.cut(nota_uni, bins=bins, labels=labels, include_lowest=True).value_counts().sort_index()
freq_multi = pd.cut(nota_multi, bins=bins, labels=labels, include_lowest=True).value_counts().sort_index()

df_tabela = pd.DataFrame({
    'Faixa de Nota': labels,
    'Humano': freq_humano.values,
    'Uni-Agente': freq_uni.values,
    'Multi-Agente': freq_multi.values
})

print("\n" + df_tabela.to_latex(
    index=False,
    caption='Distribuição de Frequência das Notas Totais',
    label='tab:freq_notas_comparativa'
))

df_tabela.to_csv('tabela_frequencia_notas.csv', index=False)
print("Arquivo 'tabela_frequencia_notas.csv' gerado com sucesso!")