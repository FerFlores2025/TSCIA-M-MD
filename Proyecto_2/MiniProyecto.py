# MINI PROYECTO - ANÁLISIS DE RECOMPRA

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import (
    confusion_matrix, classification_report,
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, roc_curve
)


# Paso 1: Dataset del anexo (20 registros)
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


# Paso 2: Dataset ampliado (1000 registros sintéticos)

def generate_synthetic_dataset(n=1000, seed=42):
    np.random.seed(seed)
    Cliente_ID = np.arange(1, n+1)
    Genero = np.random.choice(["F", "M"], size=n, p=[0.52, 0.48])
    Edad = np.clip((np.random.normal(loc=35, scale=10, size=n)).astype(int), 18, 75)
    Ingreso_Mensual = np.clip((np.random.normal(loc=40000, scale=12000, size=n)).astype(int), 10000, 200000)
    Recibio_Promo = np.random.binomial(1, 0.5, size=n)  # 1 = Sí, 0 = No
    Monto_Promocion = (Recibio_Promo * np.random.choice([100,200,300,400,500,600,700,800,900,1000], size=n)).astype(int)
    Total_Compras = np.clip(np.random.poisson(lam=2, size=n), 0, 20)

    # Generar probabilidad de recompra con un modelo logit-like
    logit = (
        -1.0
        + 0.8 * Recibio_Promo
        + 0.002 * Monto_Promocion
        + 0.03 * Total_Compras
        - 0.01 * (Edad - 30)
        + 0.00001 * (Ingreso_Mensual - 35000)
        + np.random.normal(scale=0.5, size=n)
    )
    prob_recompra = 1 / (1 + np.exp(-logit))
    Recompra = (np.random.rand(n) < prob_recompra).astype(int)

    df = pd.DataFrame({
        "Cliente_ID": Cliente_ID,
        "Genero": Genero,
        "Edad": Edad,
        "Recibio_Promo": np.where(Recibio_Promo==1, "Sí", "No"),
        "Monto_Promocion": Monto_Promocion,
        "Recompra": np.where(Recompra==1, "Sí", "No"),
        "Total_Compras": Total_Compras,
        "Ingreso_Mensual": Ingreso_Mensual
    })
    return df

df = generate_synthetic_dataset(n=1000)
df.to_excel("Mini_Proyecto_Clientes_Promociones_expanded.xlsx", index=False)
print("Dataset ampliado guardado en Excel: Mini_Proyecto_Clientes_Promociones_expanded.xlsx")


# Paso 3: EDA
print(df.info())
print(df.describe())

# Ejemplo gráfico: histograma de edad
plt.hist(df["Edad"], bins=20)
plt.title("Distribución de Edad")
plt.show()


# Paso 4: Preprocesamiento
df["Genero_num"] = df["Genero"].map({"F":0, "M":1})
df["Recibio_Promo_num"] = df["Recibio_Promo"].map({"No":0, "Sí":1})
df["Recompra_num"] = df["Recompra"].map({"No":0, "Sí":1})


# Paso 5: Modelado (Árbol de Decisión)
X = df[["Genero_num","Edad","Recibio_Promo_num","Monto_Promocion","Total_Compras","Ingreso_Mensual"]]
y = df["Recompra_num"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

clf = DecisionTreeClassifier(max_depth=6, random_state=42)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
y_proba = clf.predict_proba(X_test)[:,1]

print("Accuracy:", accuracy_score(y_test, y_pred))
print("Precision:", precision_score(y_test, y_pred))
print("Recall:", recall_score(y_test, y_pred))
print("F1:", f1_score(y_test, y_pred))
print("ROC AUC:", roc_auc_score(y_test, y_proba))

print("\nClassification Report:\n", classification_report(y_test, y_pred))

# Matriz de confusión
cm = confusion_matrix(y_test, y_pred)
print("Matriz de Confusión:\n", cm)

plt.imshow(cm, cmap="Blues")
plt.title("Matriz de Confusión")
plt.show()

# Importancia de variables
importancias = pd.Series(clf.feature_importances_, index=X.columns)
print("\nImportancia de variables:\n", importancias)

importancias.plot(kind="barh", title="Importancia de Variables")
plt.show()

# Visualización del árbol
plt.figure(figsize=(12,6))
plot_tree(clf, feature_names=X.columns, class_names=["No","Sí"], filled=True)
plt.show()