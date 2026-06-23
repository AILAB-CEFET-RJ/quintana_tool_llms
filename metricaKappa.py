import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os
from sklearn.metrics import cohen_kappa_score, mean_squared_error, accuracy_score

# ==========================================
# CORREÇÃO DEFINITIVA: Caminhos Absolutos e Nomes Exatos
# ==========================================
# Pega o diretório exato onde este script (.py) está salvo no seu computador
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))

# Define os caminhos exatos conforme a sua imagem do VS Code
pasta_ollama = os.path.join(DIRETORIO_ATUAL, "Código dos modelos e Resultados", "Resultados")
pasta_openai = os.path.join(DIRETORIO_ATUAL, "Resultado Openai")

pastas_para_buscar = [pasta_ollama, pasta_openai]
arquivos_csv = []

for pasta in pastas_para_buscar:
    # Procura todos os resultado_completo.csv dentro de cada pasta
    padrao_busca = os.path.join(pasta, "**", "resultado_completo.csv")
    arquivos_csv.extend(glob.glob(padrao_busca, recursive=True))

# Trava de segurança para avisar se der erro
if len(arquivos_csv) == 0:
    print("❌ ERRO CRÍTICO: Nenhum arquivo 'resultado_completo.csv' foi encontrado!")
    print(f"O script procurou nestas duas pastas:\n1) {pasta_ollama}\n2) {pasta_openai}")
    exit()

lista_dfs = []
for arquivo in arquivos_csv:
    df_temp = pd.read_csv(arquivo)
    # Cria coluna com o nome da pasta para separar os modelos depois
    df_temp['seed_origem'] = os.path.basename(os.path.dirname(arquivo))
    lista_dfs.append(df_temp)

df_completo = pd.concat(lista_dfs, ignore_index=True)

# Separa em dois DataFrames (usando .copy() para garantir segurança)
df_uni = df_completo[df_completo['seed_origem'].str.contains('unico', case=False, na=False)].copy()
df_multi = df_completo[df_completo['seed_origem'].str.contains('multi', case=False, na=False)].copy()

# =====================================================================
# TRATAMENTO DE DADOS (Limpeza do "nao existe")
# =====================================================================
colunas_de_nota = [
    'nota_antiga', 'nota_nova', 
    'c1', 'c2', 'c3', 'c4', 'c5', 
    'c1_antiga', 'c2_antiga', 'c3_antiga', 'c4_antiga', 'c5_antiga'
]

# Força a conversão para número. O que for texto vira NaN (nulo)
for col in colunas_de_nota:
    if col in df_uni.columns:
        df_uni[col] = pd.to_numeric(df_uni[col], errors="coerce")
    if col in df_multi.columns:
        df_multi[col] = pd.to_numeric(df_multi[col], errors="coerce")

# Remove as linhas que ficaram com notas nulas para não quebrar o gráfico
df_uni = df_uni.dropna(subset=['nota_antiga', 'nota_nova'])
df_multi = df_multi.dropna(subset=['nota_antiga', 'nota_nova'])
# =====================================================================

def calcular_metricas(y_true, y_pred, nome_modelo):
    qwk = cohen_kappa_score(y_true, y_pred, weights="quadratic")
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    acuracia = accuracy_score(y_true, y_pred)
    
    return {
        "Modelo": nome_modelo,
        "QWK (Kappa)": round(qwk, 4),
        "RMSE": round(rmse, 2),
        "Acurácia": round(acuracia, 4)
    }

# Métricas Globais
res_uni = calcular_metricas(df_uni["nota_antiga"], df_uni["nota_nova"], "Uni-Agente")
res_multi = calcular_metricas(df_multi["nota_antiga"], df_multi["nota_nova"], "Multi-Agente")

df_resultados = pd.DataFrame([res_uni, res_multi])
print("--- RESULTADOS GLOBAIS ---")
print(df_resultados)

# Geração dos Gráficos
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
sns.scatterplot(x=df_uni["nota_antiga"], y=df_uni["nota_nova"], alpha=0.6)
plt.plot([0, 1000], [0, 1000], "r--")
plt.title(f"Uni-Agente (QWK={res_uni['QWK (Kappa)']})")
plt.xlabel("Nota Humana")
plt.ylabel("Nota IA")
plt.grid(alpha=0.3)

plt.subplot(1, 2, 2)
sns.scatterplot(x=df_multi["nota_antiga"], y=df_multi["nota_nova"], alpha=0.6)
plt.plot([0, 1000], [0, 1000], "r--")
plt.title(f"Multi-Agente (QWK={res_multi['QWK (Kappa)']})")
plt.xlabel("Nota Humana")
plt.ylabel("Nota IA")
plt.grid(alpha=0.3)

plt.tight_layout()
plt.savefig("comparacao_modelos.png", dpi=300)
plt.show()

# Métricas por Competência
competencias = ["c1", "c2", "c3", "c4", "c5"]
dados_comp = []

for c in competencias:
    temp_uni = df_uni[[f"{c}_antiga", c]].dropna()
    temp_multi = df_multi[[f"{c}_antiga", c]].dropna()
    
    k_uni = cohen_kappa_score(temp_uni[f"{c}_antiga"], temp_uni[c], weights="quadratic")
    k_multi = cohen_kappa_score(temp_multi[f"{c}_antiga"], temp_multi[c], weights="quadratic")
    
    dados_comp.append({
        "Competência": c.upper(),
        "Kappa Uni": round(k_uni, 4),
        "Kappa Multi": round(k_multi, 4)
    })

df_comp = pd.DataFrame(dados_comp)
print("\n--- RESULTADOS POR COMPETÊNCIA ---")
print(df_comp)

# Exportar para Excel
with pd.ExcelWriter("avaliacao_final_modelos.xlsx") as writer:
    df_resultados.to_excel(writer, sheet_name="Resumo Geral", index=False)
    df_comp.to_excel(writer, sheet_name="Por Competência", index=False)