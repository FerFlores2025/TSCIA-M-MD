# Caraga las librerias necesarias

import pandas as pd #importa la libreria pandas,usada para leer datos(csv)
import mysql.connector # permite conectarse a base de datos MYSQL desde PYTHON.
from mysql.connector import Error # importa la clase de error para manejar errores que ocurran al conctarse o ejecutar consultas.
from pathlib import Path #permite trabajar con rutas de arhivos(ubicar los CSV en carpetas)
import logging # se usa para registrar mensajes en consola (informacion, errores)de manera mas profecional.

# Configurar logging(el sistema logs: son menasajes imformativos)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')#muestra mensajes informativos y errores( muestra la fecha, l hora, INFO:CONEXION ESTABLECIDA CON EXITO)
logger = logging.getLogger(__name__)  # Crea un "registrador" que vas a usar dentro de la clase para mostrar mensajes

# Crea una clase llamada MYSQLIMPORTER(quen agrupa todola logica para conectarse a MYSQL y cargar los ARCHIVOS CSV)
class MySQLImporter:
    """Clase para importar múltiples CSVs a MySQL""" #Este es un texto llamado, DOCSTRING. ES UNA DESCRIPCION DE LO QUE HACE LA CLASE.
    
    def __init__(self, host, user, password, database, port=3306): #__int__ es el metodo constructor(ejecuta automaticamente cuando creas un objeto de clase)
        self.host = host # estos lineas son los parametros  de conexion de MYSQL
        self.user = user # self. (guarda los valores dentro de objeto, para poder usarlos en otros metodos.)
        self.password = password
        self.database = database
        self.port = port
        self.connection = None # indica si inicialmente no hay conexion abierta.
    
    def conectar(self):  #define un metodo llamado conector que intenta abrir la conexion con la base.
        """Establece conexión con MySQL"""
        try:   # usa mysql.connector.connect(), y sele pasan los datos que ya guarde(self.host,self.user,etc).
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                charset='utf8mb4',
                autocommit=False
            )
            logger.info(f" Conexión exitosa a la base de datos '{self.database}'") # si laconexion es exitosa se guarda en self.connection
            return True
        except Error as e:
            logger.error(f" Error al conectar a MySQL: {e}")
            return False
    
    def desconectar(self):  # declara un metodo dentro de la clase para cerrar la coneccion con la base MYSQL-
        """Cierra la conexión"""  # es un DOCSTRING(es decir una pequeña descripcion del metodo)
        if self.connection and self.connection.is_connected():  # resvisa si existe la coneccion y si realmente esta activa.
            self.connection.close()  #cierra la conexion.
            logger.info(" Conexión cerrada") # muestra un mensaje en consola que la conexion fue cerrada correctamente.
    
    def leer_csv(self, ruta_archivo, modo='skip'):  # crea un metodo que lee un archivo CSV desde una ruta que le pasas como argumento.
        """Lee un CSV con manejo robusto de errores"""  # doctring que explica el proposito de la funcion.
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1'] #crea una lista de posibles codificadores de texto(es util para los CSV que viene con acento o caracteres raros segun el sistema donde se genraron)
        
        for enc in encodings:  #inicia un bucle que intentara leer los CSV con el enconding actual.
            try:  #usa panda para leer los CSV
                df = pd.read_csv(
                    ruta_archivo, # ubicacion del archivo.
                    encoding=enc, #usa la codificacion actual del bucle.
                    sep=',',  # separador de columnas.
                    quotechar='"',
                    escapechar='\\',
                    on_bad_lines=modo, #si hay errores en las filas las saltea.
                    engine='python',
                    skipinitialspace=True  # elimina espacios extra al inicio de los datos.
                )
                logger.info(f" CSV leído: {len(df)} filas con encoding {enc}")  #muetras un msj informando cuantas filas se leyeron y con que codificacion funciona.
                return df  #devuelve el dataframe leido, si todo salio bien.
            except UnicodeDecodeError: #si el archivo no se puede codificar con el enconding actual, entra aca.
                continue # pasa al siguiente encondig de la lista. para volver a intentar.
            except Exception as e:  # cptura cual error inesperado.
                logger.error(f"Error con encoding {enc}: {e}")  #muestra un msj de error en la consola.
                
                continue
        
        raise ValueError(f" No se pudo leer el CSV: {ruta_archivo}")
    
    def tabla_existe(self, nombre_tabla):
        """Verifica si una tabla existe en la base de datos"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SHOW TABLES LIKE '{nombre_tabla}'")
            resultado = cursor.fetchone()
            return resultado is not None
        finally:
            cursor.close()
    
    def crear_tabla_desde_df(self, df, nombre_tabla, clave_primaria):
        """Crea una tabla en MySQL basándose en el DataFrame"""
        cursor = self.connection.cursor()
        
        try:
            # Verificar si la tabla ya existe
            cursor.execute(f"SHOW TABLES LIKE '{nombre_tabla}'")
            tabla_existe = cursor.fetchone() is not None
            
            if tabla_existe:
                # Verificar si tiene PRIMARY KEY
                cursor.execute(f"""
                    SELECT COLUMN_NAME 
                    FROM information_schema.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = '{self.database}' 
                    AND TABLE_NAME = '{nombre_tabla}' 
                    AND CONSTRAINT_NAME = 'PRIMARY'
                """)
                pk_existente = cursor.fetchone()
                
                if pk_existente:
                    logger.info(f" Tabla '{nombre_tabla}' ya existe con PRIMARY KEY: {pk_existente[0]}")
                else:
                    logger.warning(f"  Tabla '{nombre_tabla}' existe pero SIN PRIMARY KEY")
                    # Intentar agregar PRIMARY KEY
                    try:
                        cursor.execute(f"ALTER TABLE `{nombre_tabla}` ADD PRIMARY KEY (`{clave_primaria}`)")
                        self.connection.commit()
                        logger.info(f" PRIMARY KEY agregada a '{nombre_tabla}'")
                    except Exception as e:
                        logger.error(f" No se pudo agregar PRIMARY KEY: {e}")
                return
            
            # Mapear tipos de pandas a MySQL
            tipo_mysql = {
                'int64': 'INT',
                'float64': 'DECIMAL(10,2)',
                'object': 'VARCHAR(255)',
                'datetime64': 'DATETIME',
                'bool': 'BOOLEAN'
            }
            
            # Construir definición de columnas
            columnas_sql = []
            for col in df.columns:
                tipo_pandas = str(df[col].dtype)
                tipo_sql = tipo_mysql.get(tipo_pandas, 'TEXT')
                
                if col == clave_primaria:
                    columnas_sql.append(f"`{col}` {tipo_sql} PRIMARY KEY")
                else:
                    columnas_sql.append(f"`{col}` {tipo_sql}")
            
            # Crear tabla con PRIMARY KEY explícita
            sql = f"CREATE TABLE `{nombre_tabla}` ({', '.join(columnas_sql)})"
            cursor.execute(sql)
            self.connection.commit()
            logger.info(f" Tabla '{nombre_tabla}' creada con PRIMARY KEY en '{clave_primaria}'")
            
        except Exception as e:
            logger.error(f" Error al crear tabla '{nombre_tabla}': {e}")
            raise
        finally:
            cursor.close()
    
    def limpiar_duplicados(self, nombre_tabla, clave_primaria):
        """Elimina filas duplicadas manteniendo solo la primera ocurrencia"""
        cursor = self.connection.cursor()
        
        try:
            # Contar duplicados antes
            cursor.execute(f"""
                SELECT COUNT(*) - COUNT(DISTINCT `{clave_primaria}`) 
                FROM `{nombre_tabla}`
            """)
            duplicados_antes = cursor.fetchone()[0]
            
            if duplicados_antes == 0:
                logger.info(f" No hay duplicados en '{nombre_tabla}'")
                return
            
            logger.warning(f"  Encontrados {duplicados_antes} registros duplicados en '{nombre_tabla}'")
            
            # Crear tabla temporal con datos únicos
            cursor.execute(f"""
                CREATE TEMPORARY TABLE temp_{nombre_tabla} AS
                SELECT * FROM `{nombre_tabla}`
                GROUP BY `{clave_primaria}`
            """)
            
            # Vaciar tabla original
            cursor.execute(f"TRUNCATE TABLE `{nombre_tabla}`")
            
            # Reinsertar datos únicos
            cursor.execute(f"""
                INSERT INTO `{nombre_tabla}`
                SELECT * FROM temp_{nombre_tabla}
            """)
            
            # Eliminar tabla temporal
            cursor.execute(f"DROP TEMPORARY TABLE temp_{nombre_tabla}")
            
            self.connection.commit()
            logger.info(f" {duplicados_antes} duplicados eliminados de '{nombre_tabla}'")
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f" Error al limpiar duplicados: {e}")
        finally:
            cursor.close()
    
    def insertar_datos_bulk(self, df, nombre_tabla, clave_primaria):
        """Inserta o actualiza datos usando ON DUPLICATE KEY UPDATE"""
        if not self.connection:
            raise ConnectionError("No hay conexión activa")
        
        cursor = self.connection.cursor()
        
        try:
            # Verificar que hay PRIMARY KEY definida
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = '{self.database}' 
                AND TABLE_NAME = '{nombre_tabla}' 
                AND CONSTRAINT_NAME = 'PRIMARY'
            """)
            tiene_pk = cursor.fetchone()[0] > 0
            
            if not tiene_pk:
                logger.error(f" La tabla '{nombre_tabla}' NO tiene PRIMARY KEY definida")
                logger.error("   Los datos se duplicarán en cada ejecución")
                raise ValueError(f"Tabla '{nombre_tabla}' requiere PRIMARY KEY para evitar duplicados")
            
            columnas = list(df.columns)
            cols_str = ", ".join(f"`{col}`" for col in columnas)
            placeholders = ", ".join(["%s"] * len(columnas))
            
            # Columnas para UPDATE (excluir clave primaria)
            update_cols = [col for col in columnas if col != clave_primaria]
            
            if update_cols:  # Solo si hay columnas para actualizar
                update_str = ", ".join(f"`{col}` = VALUES(`{col}`)" for col in update_cols)
                
                # Query con ON DUPLICATE KEY UPDATE
                sql = f"""
                    INSERT INTO `{nombre_tabla}` ({cols_str})
                    VALUES ({placeholders})
                    ON DUPLICATE KEY UPDATE {update_str}
                """
            else:
                # Si solo hay clave primaria, usar INSERT IGNORE
                sql = f"""
                    INSERT IGNORE INTO `{nombre_tabla}` ({cols_str})
                    VALUES ({placeholders})
                """
            
            # Convertir DataFrame a lista de tuplas (manejar NaN)
            datos = [tuple(None if pd.isna(val) else val for val in row) 
                     for row in df.values]
            
            # Ejecutar en lote
            cursor.executemany(sql, datos)
            filas_afectadas = cursor.rowcount
            self.connection.commit()
            
            logger.info(f" Procesadas {len(datos)} filas en '{nombre_tabla}' ({filas_afectadas} afectadas)")
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f" Error al insertar en '{nombre_tabla}': {e}")
            raise
        finally:
            cursor.close()
    
    def importar_csv_completo(self, ruta_csv, nombre_tabla, clave_primaria, crear_tabla=True, limpiar_duplicados=False):
        """Importa un CSV completo a una tabla MySQL"""
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f" Procesando: {Path(ruta_csv).name}")
            logger.info(f" Tabla destino: {nombre_tabla}")
            logger.info(f" Clave primaria: {clave_primaria}")
            
            # 1. Leer CSV
            df = self.leer_csv(ruta_csv)
            
            # Verificar que existe la clave primaria
            if clave_primaria not in df.columns:
                raise ValueError(f" La columna '{clave_primaria}' no existe en el CSV. "
                               f"Columnas disponibles: {list(df.columns)}")
            
            logger.info(f" Columnas: {list(df.columns)}")
            
            # 2. Crear tabla si no existe
            if crear_tabla:
                self.crear_tabla_desde_df(df, nombre_tabla, clave_primaria)
            
            # 3. Limpiar duplicados existentes (opcional)
            if limpiar_duplicados:
                self.limpiar_duplicados(nombre_tabla, clave_primaria)
            
            # 4. Insertar datos
            self.insertar_datos_bulk(df, nombre_tabla, clave_primaria)
            
            logger.info(f" Importación completada: {nombre_tabla}")
            return True
            
        except Exception as e:
            logger.error(f" Error al importar {ruta_csv}: {e}")
            return False


def main():
    # ==================== CONFIGURACIÓN ====================
    
    # Configuración de la base de datos
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'supermercado',
        'port': 3306
    }
    
    # Carpeta donde están tus CSVs
    CARPETA_CSV = r"C:\Users\Fer\OneDrive\Escritorio\Modelado de Mineria de Datos\proyecto_1\supermercado"
    
    # Lista de archivos CSV a importar
    # Formato: (nombre_archivo, nombre_tabla, clave_primaria)
    ARCHIVOS_A_IMPORTAR = [
        ('clientes.csv', 'clientes', 'id_cliente'),
        ('productos.csv', 'productos', 'id_producto'),
        ('rubros.csv', 'rubros', 'id_rubro'),
        ('venta.csv', 'venta', 'id_venta'),
        ('supermercado.csv', 'supermercado', 'id'),
        ('sucursal.csv' , 'sucursal', 'id_sucursal')
        # Agrega más archivos aquí siguiendo el mismo formato
    ]
    
    # Opción: crear tablas automáticamente si no existen
    CREAR_TABLAS = True
    
    # NUEVO: Limpiar duplicados antes de importar (poner True si ya hay datos duplicados)
    LIMPIAR_DUPLICADOS_EXISTENTES = True  # Cambiar a False después de la primera ejecución
    
    # ==================== EJECUCIÓN ====================
    
    print("\n" + "="*60)
    print(" IMPORTADOR DE CSVs A MYSQL")
    print("="*60)
    
    importer = MySQLImporter(**DB_CONFIG)
    
    # Conectar a la base de datos
    if not importer.conectar():
        logger.error(" No se pudo conectar a MySQL. Verifica las credenciales.")
        return
    
    # Contador de éxitos y fallos
    exitosos = 0
    fallidos = 0
    
    # Procesar cada archivo
    for nombre_archivo, nombre_tabla, clave_primaria in ARCHIVOS_A_IMPORTAR:
        ruta_completa = Path(CARPETA_CSV) / nombre_archivo
        
        # Verificar si el archivo existe
        if not ruta_completa.exists():
            logger.warning(f"  Archivo no encontrado: {nombre_archivo} - SALTANDO")
            fallidos += 1
            continue
        
        # Importar el CSV
        if importer.importar_csv_completo(ruta_completa, nombre_tabla, clave_primaria, 
                                          CREAR_TABLAS, LIMPIAR_DUPLICADOS_EXISTENTES):
            exitosos += 1
        else:
            fallidos += 1
    
    # Resumen final
    print("\n" + "="*60)
    print(" RESUMEN DE IMPORTACIÓN")
    print("="*60)
    print(f" Exitosos: {exitosos}")
    print(f" Fallidos: {fallidos}")
    print(f" Total procesados: {exitosos + fallidos}")
    print("="*60 + "\n")
    
    # Cerrar conexión
    importer.desconectar()
    logger.info(" Proceso finalizado")


if __name__ == "__main__":
    main()