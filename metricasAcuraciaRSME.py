import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, accuracy_score

arquivo_uni = "Resultados\Redações Uni-agente.xlsx"
arquivo_multi = "Resultados\Redações Multi-Agente.xlsx"

df_uni = pd.read_excel(arquivo_uni)
df_multi = pd.read_excel(arquivo_multi)

y_true_uni = df_uni["nota_antiga"]
y_pred_uni = df_uni["nota_nova"]

rmse_uni = np.sqrt(mean_squared_error(y_true_uni, y_pred_uni))
acc_uni = accuracy_score(y_true_uni, y_pred_uni)

df_metricas_uni = pd.DataFrame({
    "Modelo": ["Uni-Agente"],
    "RMSE": [rmse_uni],
    "Acuracia": [acc_uni]
})

df_metricas_uni.to_excel("metricas_uni_agente.xlsx", index=False)

y_true_multi = df_multi["nota_original_total"]
y_pred_multi = df_multi["nota_agregador_validada_total"]

rmse_multi = np.sqrt(mean_squared_error(y_true_multi, y_pred_multi))
acc_multi = accuracy_score(y_true_multi, y_pred_multi)

df_metricas_multi = pd.DataFrame({
    "Modelo": ["Multi-Agente"],
    "RMSE": [rmse_multi],
    "Acuracia": [acc_multi]
})

df_metricas_multi.to_excel("metricas_multi_agente.xlsx", index=False)
