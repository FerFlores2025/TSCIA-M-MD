# streamlit run DashboardMiniProyecto.py


import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, confusion_matrix

data_anexo = {
    "Cliente_ID": list(range(1, 21)),
    "Genero": ["F", "M"] * 10,
    "Edad": [23, 34, 45, 29, 31, 38, 27, 50, 40, 36,
             25, 33, 46, 28, 39, 42, 30, 48, 35, 37],
    "Recibio_Promo": ["Sí", "No", "Sí", "Sí", "No", "Sí", "No", "Sí", "No", "Sí",
                      "No", "Sí", "Sí", "No", "No", "Sí", "No", "Sí", "No", "Sí"],
    "Monto_Promocion": [500, 0, 700, 300, 0, 600, 0, 800, 0, 450,
                        0, 620, 710, 0, 0, 480, 0, 750, 0, 520],
    "Recompra": ["Sí", "No", "Sí", "No", "No", "Sí", "No", "Sí", "No", "Sí",
                 "No", "No", "Sí", "No", "No", "Sí", "No", "Sí", "No", "Sí"],
    "Total_Compras": [2, 1, 3, 1, 1, 4, 1, 5, 1, 3,
                      1, 2, 4, 1, 1, 3, 1, 5, 1, 3],
    "Ingreso_Mensual": [30000, 45000, 40000, 28000, 32000, 50000, 31000, 60000,
                        29000, 37000, 31000, 34000, 47000, 30000, 29000, 43000,
                        33000, 55000, 30000, 41000]
}
df_anexo = pd.DataFrame(data_anexo)
df_anexo.to_excel("Mini_Proyecto_Clientes_Promociones.xlsx", index=False)
print("Dataset anexo guardado en Excel: Mini_Proyecto_Clientes_Promociones.xlsx")





# -----------------------
# Cargar datos
# -----------------------
df = pd.read_excel("Mini_Proyecto_Clientes_Promociones.xlsx")

# Preprocesamiento rápido
df["Genero_num"] = df["Genero"].map({"F":0, "M":1})

df["Recibio_Promo_num"] = df["Recibio_Promo"].map({"No":0, "Sí":1})
df["Recompra_num"] = df["Recompra"].map({"No":0, "Sí":1})

# -----------------------
# Configuración del Dashboard
# -----------------------
st.set_page_config(page_title="Dashboard Recompra", layout="wide")

st.title(" Dashboard de Recompra en Marketing")
st.markdown("Este dashboard muestra análisis exploratorio y resultados del modelo de predicción de *recompra*.")

# -----------------------
# Panel lateral de filtros
# -----------------------
st.sidebar.header("Filtros")

# Filtro por género
genero_filter = st.sidebar.multiselect("Género", df["Genero"].unique(), default=df["Genero"].unique())
df_filtered = df[df["Genero"].isin(genero_filter)]

# Filtro por rango de edad
edad_range = st.sidebar.slider("Edad", int(df["Edad"].min()), int(df["Edad"].max()), 
                               (int(df["Edad"].min()), int(df["Edad"].max())))
df_filtered = df_filtered[(df_filtered["Edad"] >= edad_range[0]) & (df_filtered["Edad"] <= edad_range[1])]

# -----------------------
# Análisis Exploratorio
# -----------------------
st.subheader(" Distribución de Variables")

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots()
    sns.histplot(df_filtered["Edad"], bins=20, kde=True, ax=ax)
    ax.set_title("Distribución de Edad")
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots()
    sns.boxplot(x="Recompra", y="Monto_Promocion", data=df_filtered, ax=ax)
    ax.set_title("Monto de Promoción vs Recompra")
    st.pyplot(fig)

# -----------------------
# Modelo predictivo
# -----------------------
st.subheader(" Modelo Predictivo (Árbol de Decisión)")

X = df[["Genero_num","Edad","Recibio_Promo_num","Monto_Promocion","Total_Compras","Ingreso_Mensual"]]
y = df["Recompra_num"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

clf = DecisionTreeClassifier(max_depth=6, random_state=42)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_test)

acc = accuracy_score(y_test, y_pred)

st.write(f"*Accuracy del modelo:* {acc:.2f}")

# Matriz de confusión
cm = confusion_matrix(y_test, y_pred)
fig, ax = plt.subplots()
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["No","Sí"], yticklabels=["No","Sí"], ax=ax)
ax.set_title("Matriz de Confusión")
st.pyplot(fig)

# -----------------------
# Predicción individual
# -----------------------
st.subheader("Predicción de un Cliente Nuevo")

genero_input = st.selectbox("Género", ["F","M"])
edad_input = st.slider("Edad", 18, 75, 30)
promo_input = st.selectbox("Recibió Promo", ["No","Sí"])
monto_input = st.number_input("Monto Promoción", min_value=0, max_value=2000, value=500)
compras_input = st.slider("Total Compras", 0, 20, 2)
ingreso_input = st.number_input("Ingreso Mensual", min_value=5000, max_value=200000, value=40000)

nuevo_cliente = pd.DataFrame({
    "Genero_num":[0 if genero_input=="F" else 1],
    "Edad":[edad_input],
    "Recibio_Promo_num":[0 if promo_input=="No" else 1],
    "Monto_Promocion":[monto_input],
    "Total_Compras":[compras_input],
    "Ingreso_Mensual":[ingreso_input]
})

prediccion = clf.predict(nuevo_cliente)[0]
resultado = " Recomienda Recompra" if prediccion==1 else "❌ No Recompra"

st.write(f"*Resultado del modelo:* {resultado}")
