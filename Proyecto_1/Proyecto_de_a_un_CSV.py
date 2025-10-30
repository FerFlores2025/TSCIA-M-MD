import pandas as pd
import os

# Nombre del archivo CSV

ARCHIVO = r"C:\\Users\\Fer\\OneDrive\\Escritorio\\Modelado de Mineria de Datos\\Proyecto_1\\supermercado\\producto.csv"

def listar_csv():
    archivos = [f for f in os.listdir(ARCHIVO)if f.endswith(".csv")]
    return archivos

# --- Funciones ---
def cargar_datos(archivo):
    ruta = os.path.join(ARCHIVO, archivo)
    try:
        df = pd.read_csv(ARCHIVO)
        print(f"Archivo {ARCHIVO} cargado con éxito ")
    except FileNotFoundError:
        print(f"El archivo {ARCHIVO} no existe, se creará uno nuevo al guardar.")
        df = pd.DataFrame()  # vacío
    return df

def guardar_datos(df):
    df.to_csv(ARCHIVO, index=False)
    print("Cambios guardados en el archivo ")

def mostrar_datos(df):
    if df.empty:
        print("No hay datos cargados.")
    else:
        print("\n--- DATOS ACTUALES ---")
        print(df)

def insertar_registro(df):
    if df.empty:
        print("No se puede insertar porque no hay columnas definidas en el CSV.")
        return df
    nuevo = {}
    for col in df.columns:
        nuevo[col] = input(f"Ingrese valor para {col}: ")
    df.loc[len(df)] = nuevo
    print("Registro insertado ")
    return df

def modificar_registro(df):
    if df.empty:
        print("No hay registros para modificar.")
        return df
    mostrar_datos(df)
    try:
        indice = int(input("Ingrese el índice (fila) a modificar: "))
        if 0 <= indice < len(df):
            for col in df.columns:
                nuevo = input(f"{col} (actual: {df.at[indice, col]}): ")
                if nuevo != "":
                    df.at[indice, col] = nuevo
            print("Registro modificado ")
        else:
            print("Índice fuera de rango.")
    except ValueError:
        print("Debe ingresar un número válido.")
    return df

def eliminar_registro(df):
    if df.empty:
        print("No hay registros para eliminar.")
        return df
    mostrar_datos(df)
    try:
        indice = int(input("Ingrese el índice (fila) a eliminar: "))
        if 0 <= indice < len(df):
            df = df.drop(indice).reset_index(drop=True)
            print("Registro eliminado ")
        else:
            print("Índice fuera de rango.")
    except ValueError:
        print("Debe ingresar un número válido.")
    return df

# --- Programa principal ---
def main():
    df = cargar_datos(ARCHIVO)

    while True:
        print("\n--- MENÚ ---")
        print("1. Mostrar datos")
        print("2. Insertar registro")
        print("3. Modificar registro")
        print("4. Eliminar registro")
        print("5. Guardar y salir")

        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            mostrar_datos(df)
        elif opcion == "2":
            df = insertar_registro(df)
        elif opcion == "3":
            df = modificar_registro(df)
        elif opcion == "4":
            df = eliminar_registro(df)
        elif opcion == "5":
            guardar_datos(df)
            print(" Programa finalizado.")
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    main()

