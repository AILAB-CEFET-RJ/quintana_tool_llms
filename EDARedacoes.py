import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob

# 1. Carregar todos os arquivos .jsonl
caminho_arquivos = "Redações/*.jsonl"
arquivos_jsonl = glob.glob(caminho_arquivos)

dfs = []
for arquivo in arquivos_jsonl:
    df_temp = pd.read_json(arquivo, lines=True)
    dfs.append(df_temp)

# Concatena todos os arquivos em um único DataFrame
df = pd.concat(dfs, ignore_index=True)
print(f"Total de redações carregadas: {len(df)}\n")

# =====================================================================
# 2. TRATAMENTO DE DADOS (CONVERSÃO PARA PADRÃO ENEM)
# =====================================================================
# As chaves originais do seu JSON
colunas_originais = ['label_C1', 'label_C2', 'label_C3', 'label_C4', 'label_C5']
# Como queremos que elas apareçam no gráfico
colunas_competencias = ['Competência 1', 'Competência 2', 'Competência 3', 'Competência 4', 'Competência 5']

# Multiplica o nível (0 a 5) por 40 para virar a nota oficial (0 a 200)
for original, nova in zip(colunas_originais, colunas_competencias):
    df[nova] = df[original] * 40

# Cria a coluna da nota total somando as 5 competências convertidas
df['nota_total'] = df[colunas_competencias].sum(axis=1)


# =====================================================================
# TABELA 5.1: Frequência dos Temas
# =====================================================================
print("--- TABELA 5.1: FREQUÊNCIA DOS TEMAS ---")
tabela_temas = df['tema'].value_counts().head(10)
print(tabela_temas)
print("\n" + "="*50 + "\n")

# =====================================================================
# TABELA 5.2: Distribuição da frequência das notas
# =====================================================================
print("--- TABELA 5.2: FREQUÊNCIA DAS NOTAS TOTAIS ---")
tabela_notas = df['nota_total'].value_counts().head(10)
# Convertendo para int para tirar a casa decimal (.0) e ficar igual ao TCC
tabela_notas.index = tabela_notas.index.astype(int) 
print(tabela_notas)
print("\n" + "="*50 + "\n")

# =====================================================================
# FIGURA 5.1 ALTERNATIVA: Média das Notas por Competência (Gráfico de Barras)
# =====================================================================
# Configuração visual do gráfico
plt.figure(figsize=(10, 6))

# Usamos barplot com ci='sd' para mostrar a média e o desvio padrão
sns.barplot(data=df[colunas_competencias], 
            palette="pastel", 
            edgecolor="black",
            capsize=0.1,  # Adiciona a linha horizontal na barra de erro
            errorbar='sd') # Mostra o desvio padrão

plt.title("Média das Notas Atribuídas por Competência", fontsize=14, pad=15)
plt.ylabel("Nota Média", fontsize=12)
plt.xlabel("Critérios", fontsize=12)

# Trava o eixo Y de 0 a 200 com passos de 20 para facilitar a leitura
plt.yticks(range(0, 201, 20)) 
plt.grid(axis='y', linestyle='--', alpha=0.6)

# Salva a imagem em alta resolução
plt.savefig("Figura_5_1_Media_Competencias.png", dpi=300, bbox_inches='tight')
print("Novo Gráfico de Barras gerado e salvo como 'Figura_5_1_Media_Competencias.png'!")

# Exibe o gráfico na tela
plt.show()
print("\n--- PROVA DOS NOVE: MÉDIAS EXATAS ---")
print(df[colunas_competencias].mean())