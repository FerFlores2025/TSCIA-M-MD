## Dashboard de Recompra en Marketing

Este proyecto es un **dashboard interactivo en Streamlit** que permite
analizar el comportamiento de los clientes frente a promociones y
predecir la **probabilidad de recompra** usando un modelo de árbol de
decisión.

##  Requisitos

Antes de ejecutar el dashboard, asegurate de tener instaladas las
siguientes librerías:

``` bash
pip install streamlit pandas matplotlib seaborn scikit-learn openpyxl
```

> `openpyxl` es necesario para leer archivos Excel (`.xlsx`).

##  Archivos del proyecto

-   `dashboard.py` → Script principal de Streamlit.\
-   `mini_proyecto_clientes_promociones.xlsx` → Archivo de datos con la
    información de clientes y promociones.\
-   (Opcional) `Mini_Proyecto_Clientes_Promociones_expanded.xlsx` →
    Versión extendida del dataset.

##  Cómo ejecutar

1.  Colocar el archivo Excel en la misma carpeta que el script
    `dashboard.py`.\
2.  En la terminal, ir a la carpeta del proyecto y correr:

``` bash
streamlit run dashboard.py
```

3.  Se abrirá automáticamente en tu navegador en la dirección:

        http://localhost:8501

##  Funcionalidades

-   **Filtros interactivos:** por género y rango de edad.\
-   **Visualizaciones:**
    -   Distribución de edades.\
    -   Relación entre monto de promoción y recompra.\
-   **Modelo predictivo (Árbol de Decisión):**
    -   Entrenamiento con los datos cargados.\
    -   Métricas de accuracy y matriz de confusión.\
-   **Predicción individual:** permite ingresar datos de un cliente
    nuevo y obtener si es probable que **recompre o no**.
