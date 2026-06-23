import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
import glob
import os

# =====================================================================
# 1. COLE AQUI O LINK INTEIRO DA SUA PASTA PRINCIPAL
# =====================================================================
CAMINHO_RAIZ = r"C:\Users\Usuário\Downloads\Modelos-multi-e-uniagente-2025---TCC---Danilo-Lucas-Matheus-main\Modelos-multi-e-uniagente-2025---TCC---Danilo-Lucas-Matheus-main\Resultado Openai"

# O script vai procurar automaticamente em TODAS as subpastas dentro dessa raiz
padrao_busca = os.path.join(CAMINHO_RAIZ, "**", "resultado_completo.csv")
arquivos_csv = glob.glob(padrao_busca, recursive=True)

if len(arquivos_csv) == 0:
    print(f"❌ ERRO: Nenhum 'resultado_completo.csv' encontrado dentro de:\n{CAMINHO_RAIZ}")
    exit()

lista_dfs = []
for arquivo in arquivos_csv:
    df_temp = pd.read_csv(arquivo)
    df_temp['seed_origem'] = os.path.basename(os.path.dirname(arquivo))
    lista_dfs.append(df_temp)

df_completo = pd.concat(lista_dfs, ignore_index=True)

# Separa os modelos
df_uni = df_completo[df_completo['seed_origem'].str.contains('unico', case=False, na=False)].copy()
df_multi = df_completo[df_completo['seed_origem'].str.contains('multi', case=False, na=False)].copy()

# =====================================================================
# 2. DEFINIÇÃO DE STOPWORDS E FUNÇÃO DE LIMPEZA
# =====================================================================
stopwords_pt = set([
    'de','a','o','que','e','do','da','em','um','uma','para','com','não','os','as',
    'dos','das','se','na','no','como','mais','mas','foi','ao','ele','ela','por','seu',
    'sua','ter','ser','está','são','pela','pelo','ou','também','é','estão','entre','há',
    'muito','seja','isso','esse','essa','esses','essas','tem','têm','nos','nas','pode',
    'podem','será','sobre','nota','pois','apresenta','entanto','geral','alguns','algumas',
    'texto','redação','apenas','bem','bom','boa','candidato','demonstra','apresentar','deve',
    'uso','utilização','falta','necessidade','argumentos','ideias','forma','tema','proposta',
    'intervenção','competência','domínio','norma','culta','relação','melhor','pouco','ainda',
    'cada','pontos','análise','ponto','sendo','assim'
])

def limpar_e_tokenizar(texto):
    if pd.isna(texto):
        return []
    texto = re.sub(r"[^\w\s]", "", str(texto).lower())
    palavras = texto.split()
    return [p for p in palavras if p not in stopwords_pt and not p.isdigit() and len(p) > 2]

# =====================================================================
# 3. EXTRAÇÃO E CONTAGEM DE PALAVRAS
# =====================================================================
colunas_justificativa = [
    "justificativa_c1", "justificativa_c2", "justificativa_c3",
    "justificativa_c4", "justificativa_c5"
]

texto_uni = " ".join(df_uni[colunas_justificativa].fillna("").apply(lambda x: " ".join(x.astype(str)), axis=1))
tokens_uni = limpar_e_tokenizar(texto_uni)
contagem_uni = Counter(tokens_uni).most_common(10)

texto_multi = " ".join(df_multi[colunas_justificativa].fillna("").apply(lambda x: " ".join(x.astype(str)), axis=1))
tokens_multi = limpar_e_tokenizar(texto_multi)
contagem_multi = Counter(tokens_multi).most_common(10)

# =====================================================================
# 4. GERAÇÃO DOS GRÁFICOS
# =====================================================================
# Gráfico 1: Palavras Frequentes Uni-Agente
plt.figure(figsize=(8, 6))
sns.barplot(x=[x[1] for x in contagem_uni], y=[x[0] for x in contagem_uni], palette="Blues_r")
plt.title("Vocabulário Mais Frequente: Uni-Agente Openai")
plt.xlabel("Frequência")
plt.tight_layout()
plt.savefig("palavras_frequentes_uni.png", dpi=300)
plt.close()
print("✅ Gráfico 'palavras_frequentes_uni_openai.png' gerado!")

# Gráfico 2: Palavras Frequentes Multi-Agente
plt.figure(figsize=(8, 6))
sns.barplot(x=[x[1] for x in contagem_multi], y=[x[0] for x in contagem_multi], palette="Reds_r")
plt.title("Vocabulário Mais Frequente: Multi-Agente Openai")
plt.xlabel("Frequência")
plt.tight_layout()
plt.savefig("palavras_frequentes_multi_openai.png", dpi=300)
plt.close()
print("✅ Gráfico 'palavras_frequentes_multi.png' gerado!")

# Gráfico 3: Boxplot de Tamanho do Texto
df_uni["tamanho"] = df_uni[colunas_justificativa].fillna("").apply(lambda x: len(" ".join(x.astype(str)).split()), axis=1)
df_multi["tamanho"] = df_multi[colunas_justificativa].fillna("").apply(lambda x: len(" ".join(x.astype(str)).split()), axis=1)

df_plot = pd.DataFrame({
    "Modelo": ["Uni-Agente"] * len(df_uni) + ["Multi-Agente"] * len(df_multi),
    "Contagem de Palavras": pd.concat([df_uni["tamanho"], df_multi["tamanho"]], ignore_index=True)
})

plt.figure(figsize=(9, 6))
sns.boxplot(x="Modelo", y="Contagem de Palavras", data=df_plot, palette=["skyblue", "salmon"])
plt.title("Extensão das Justificativas: Uni-Agente vs Multi-Agente Openai")
plt.tight_layout()
plt.savefig("comparacao_tamanho_texto_openai.png", dpi=300)
plt.close()
print("✅ Gráfico 'comparacao_tamanho_texto_openai.png' gerado!")