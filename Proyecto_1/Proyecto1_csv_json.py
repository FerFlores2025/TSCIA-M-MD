import pandas as pd
import os

# Carpeta principal donde están los CSV originales
CARPETA_SUPER = r"C:\Users\Fer\OneDrive\Escritorio\Modelado de Mineria de Datos\Proyecto_1\supermercado"

# Carpetas de salida
CARPETA_EXCEL = os.path.join(CARPETA_SUPER, "archivos_excel")
CARPETA_JSON = os.path.join(CARPETA_SUPER, "archivos_json")
CARPETA_CSV = os.path.join(CARPETA_SUPER, "archivos_csv")

# --- Crear carpetas si no existen ---
for carpeta in [CARPETA_EXCEL, CARPETA_JSON, CARPETA_CSV]:
    os.makedirs(carpeta, exist_ok=True)


# --- Listar los archivos CSV dentro de la carpeta supermercado ---
def listar_csv():
    archivos = [f for f in os.listdir(CARPETA_SUPER) if f.endswith(".csv")]
    return archivos

# --- Cargar y convertir cada archivo ---
def convertir_archivos():
    archivos_csv = listar_csv()

    if not archivos_csv:
        print(" No se encontraron archivos CSV en la carpeta.")
        return

    for archivo in archivos_csv:
        ruta_csv = os.path.join(CARPETA_SUPER, archivo)
        nombre_base = os.path.splitext(archivo)[0]  # quita la extensión .csv

        try:
            df = pd.read_csv(ruta_csv)
            print(f" Archivo '{archivo}' cargado correctamente.")

            # Guardar como Excel
            ruta_excel = os.path.join(CARPETA_EXCEL, f"{nombre_base}.xlsx")
            df.to_excel(ruta_excel, index=False)

            # Guardar como JSON
            ruta_json = os.path.join(CARPETA_JSON, f"{nombre_base}.json")
            df.to_json(ruta_json, orient="records", indent=4)

            # Guardar copia en carpeta CSV
            ruta_csv_salida = os.path.join(CARPETA_CSV, archivo)
            df.to_csv(ruta_csv_salida, index=False)

            print(f"  Convertido a Excel, JSON y CSV en sus respectivas carpetas.\n")

        except Exception as e:
            print(f" Error al procesar {archivo}: {e}")

# --- Ejecutar ---
if __name__== "__main__":
    convertir_archivos()
    print(" Conversión completada. Los archivos se guardaron en sus carpetas correspondientes.")






