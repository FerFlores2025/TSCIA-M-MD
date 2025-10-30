import pandas as pd
import os

# Carpeta donde están los CSV
CARPETA = r"C:\\Users\\Fer\\OneDrive\\Escritorio\\Modelado de Mineria de Datos\\Proyecto_1\\supermercado"

def listar_csv():
    archivos = [f for f in os.listdir(CARPETA) if f.endswith(".csv")]
    return archivos

def cargar_datos(archivo):
    ruta= os.path.join(CARPETA, archivo)
    try:
        df = pd.read_csv(ruta)
        print(f"Archivo {archivo} cargado con éxito ")
    except FileNotFoundError:
        print(f"El archivo {archivo} no existe, se creará uno nuevo al guardar.")
        df = pd.DataFrame()
    return df, ruta

def guardar_datos(df, ruta):
    df.to_csv(ruta, index=False)
    print("Cambios guardados en el archivo ")
    
def mostrar_datos(df):
    if df.empty:
        print("No hay datos cargados.")
    else:
        print("\n--- DATOS ACTUALES ---")
        print(df)

def insertar_registro(df):
    if df.empty:
        print(" No se puede insertar porque no hay columnas definidas en el CSV.")
        return df
    nuevo = {}
    for col in df.columns:
        nuevo[col] = input(f"Ingrese valor para {col}: ")
    df.loc[len(df)] = nuevo
    print("Registro insertado ")
    return df

def modificar_registro(df):
    if df.empty:
        print(" No hay registros para modificar.")
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
            print("Registro eliminado 9")
        else:
            print("Índice fuera de rango.")
    except ValueError:
        print("Debe ingresar un número válido.")
    return df

# --- Programa principal ---
def main():
    print("=== GESTOR DE CSV ===")

    archivos = listar_csv()
    if not archivos:
        print("No hay archivos CSV en la carpeta.")
        return
    
    print("\nArchivos disponibles:")
    for i, f in enumerate(archivos):
        print(f"{i+1}. {f}")

    try:
        opcion = int(input("\nSeleccione el número del archivo a abrir: ")) - 1
        archivo = archivos[opcion]
    except (ValueError, IndexError):
        print("Opción inválida.")
        return

    df, ruta = cargar_datos(archivo)

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
            guardar_datos(df, ruta)
            print(" Programa finalizado.")
            break
        else:
            print("Opción no válida.")

if __name__== "__main__":
    main()
