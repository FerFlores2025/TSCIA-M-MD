import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import json
import io
import base64
from datetime import datetime
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Supermercado",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #2e86ab;
        border-bottom: 2px solid #2e86ab;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2e86ab;
        margin-bottom: 1rem;
    }
    .stButton button {
        width: 100%;
        background-color: #2e86ab;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header">🛒 Dashboard Supermercado</h1>', unsafe_allow_html=True)

# Sidebar para navegación
st.sidebar.title("Navegación")
seccion = st.sidebar.radio(
    "Selecciona una sección:",
    [" Resumen General", " Gráficos Combinados", " Gestión de Datos", " Descargas"]
)

# Configuración de la carpeta de datos
carpeta = r"C:\Users\Fer\OneDrive\Escritorio\Modelado de Mineria de Datos\Proyecto_3\supermercado"

# --- FUNCIONES AUXILIARES ---
@st.cache_data
def cargar_tablas():
    """Carga todos los CSV y los procesa"""
    archivos_csv = glob.glob(os.path.join(carpeta, "*.csv"))
    dataframes = {}
    
    for archivo in archivos_csv:
        nombre = os.path.splitext(os.path.basename(archivo))[0]
        try:
            df = pd.read_csv(archivo)
            # Limpiar nombres de columnas
            df.columns = df.columns.str.replace('"', '').str.strip()
            dataframes[nombre] = df
        except Exception as e:
            st.error(f"Error cargando {nombre}: {e}")
    
    return dataframes

def convertir_df_csv(df):
    """Convierte DataFrame a CSV para descarga"""
    return df.to_csv(index=False).encode('utf-8')

def convertir_df_json(df):
    """Convierte DataFrame a JSON para descarga"""
    return df.to_json(orient='records', indent=4).encode('utf-8')

def convertir_df_excel(df):
    """Convierte DataFrame a Excel para descarga"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()

def generar_graficos_combinados(dataframes):
    """Genera gráficos combinados en memoria para el dashboard"""
    graficos = {}
    
    # Identificar tablas clave
    factura_detalle_df = dataframes.get('factura_detalle')
    producto_df = dataframes.get('producto')
    factura_enunciado_df = dataframes.get('factura_enunciado')
    rubros_df = dataframes.get('rubros')
    venta_df = dataframes.get('venta')
    cliente_df = dataframes.get('cliente')
    
    if factura_detalle_df is None or producto_df is None:
        st.error("No se encontraron las tablas necesarias para generar gráficos")
        return graficos
    
    try:
        # 1. TOP 10 PRODUCTOS MÁS VENDIDOS
        productos_vendidos = factura_detalle_df.groupby('id_producto')['cantidad'].sum().nlargest(10)
        
        if producto_df is not None:
            productos_vendidos_con_nombre = productos_vendidos.reset_index().merge(
                producto_df[['id_producto', 'nombre_producto']], 
                on='id_producto', 
                how='left'
            )
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Gráfico de barras
            ax1.bar(range(len(productos_vendidos_con_nombre)), productos_vendidos_con_nombre['cantidad'])
            ax1.set_title('Top 10 Productos Más Vendidos')
            ax1.set_xlabel('Productos')
            ax1.set_ylabel('Cantidad Vendida')
            ax1.set_xticks(range(len(productos_vendidos_con_nombre)))
            ax1.set_xticklabels(productos_vendidos_con_nombre['nombre_producto'], rotation=45, ha='right')
            
            # Gráfico de torta
            ax2.pie(productos_vendidos_con_nombre['cantidad'], labels=productos_vendidos_con_nombre['nombre_producto'], autopct='%1.1f%%')
            ax2.set_title('Distribución Top 10 Productos')
            
            plt.tight_layout()
            graficos['top10_productos'] = fig
        
        # 2. VENTAS POR RUBRO
        if rubros_df is not None:
            detalle_con_rubro = factura_detalle_df.merge(
                producto_df[['id_producto', 'id_rubro']], 
                on='id_producto', 
                how='left'
            ).merge(
                rubros_df[['id_rubro', 'nombre_rubro']], 
                on='id_rubro', 
                how='left'
            )
            
            ventas_por_rubro = detalle_con_rubro.groupby('nombre_rubro')['cantidad'].sum()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ventas_por_rubro.plot(kind='bar', color='skyblue', ax=ax)
            ax.set_title('Ventas Totales por Rubro')
            ax.set_xlabel('Rubro')
            ax.set_ylabel('Cantidad Vendida')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            graficos['ventas_por_rubro'] = fig
        
        # 3. VENTAS POR MES
        if factura_enunciado_df is not None:
            factura_enunciado_df['fecha'] = pd.to_datetime(factura_enunciado_df['fecha'])
            ventas_por_mes = factura_enunciado_df.groupby(factura_enunciado_df['fecha'].dt.to_period('M')).size()
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ventas_por_mes.plot(kind='line', marker='o', color='green', ax=ax)
            ax.set_title('Ventas por Mes')
            ax.set_xlabel('Mes')
            ax.set_ylabel('Cantidad de Ventas')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            graficos['ventas_por_mes'] = fig
        
        # 4. TICKET PROMEDIO
        if all([factura_detalle_df is not None, factura_enunciado_df is not None, venta_df is not None]):
            factura_detalle_df['total_linea'] = factura_detalle_df['cantidad'] * factura_detalle_df['precio_unitario']
            total_por_factura = factura_detalle_df.groupby('id_factura')['total_linea'].sum()
            
            ticket_info = total_por_factura.reset_index().merge(
                factura_enunciado_df[['id_factura', 'id_venta']],
                on='id_factura',
                how='left'
            ).merge(
                venta_df[['id_venta', 'id_cliente']],
                on='id_venta',
                how='left'
            )
            
            ticket_promedio = ticket_info.groupby('id_cliente')['total_linea'].mean().nlargest(10)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ticket_promedio.plot(kind='bar', color='orange', ax=ax)
            ax.set_title('Ticket Promedio por Cliente (Top 10)')
            ax.set_xlabel('ID Cliente')
            ax.set_ylabel('Ticket Promedio ($)')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            graficos['ticket_promedio'] = fig
        
        # 5. FACTURAS MÁS ALTAS
        if factura_detalle_df is not None:
            factura_detalle_df['total_linea'] = factura_detalle_df['cantidad'] * factura_detalle_df['precio_unitario']
            total_por_factura = factura_detalle_df.groupby('id_factura')['total_linea'].sum().nlargest(10)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            total_por_factura.plot(kind='bar', color='red', ax=ax)
            ax.set_title('Top 10 Facturas Más Altas')
            ax.set_xlabel('ID Factura')
            ax.set_ylabel('Monto Total ($)')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            graficos['facturas_mas_altas'] = fig
        
        # 6. PRODUCTO MÁS VENDIDO
        producto_mas_vendido = factura_detalle_df.groupby('id_producto')['cantidad'].sum().nlargest(5)
        
        if producto_df is not None:
            producto_mas_vendido_con_nombre = producto_mas_vendido.reset_index().merge(
                producto_df[['id_producto', 'nombre_producto']],
                on='id_producto',
                how='left'
            )
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(producto_mas_vendido_con_nombre['nombre_producto'], producto_mas_vendido_con_nombre['cantidad'])
            ax.set_title('Top 5 Productos Más Vendidos')
            ax.set_xlabel('Producto')
            ax.set_ylabel('Cantidad Vendida')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            graficos['producto_mas_vendido'] = fig
        
        # 7. VENTAS POR CLIENTE
        if all([factura_detalle_df is not None, factura_enunciado_df is not None, venta_df is not None]):
            factura_detalle_df['total_linea'] = factura_detalle_df['cantidad'] * factura_detalle_df['precio_unitario']
            total_por_factura = factura_detalle_df.groupby('id_factura')['total_linea'].sum()
            
            ventas_por_cliente = total_por_factura.reset_index().merge(
                factura_enunciado_df[['id_factura', 'id_venta']],
                on='id_factura',
                how='left'
            ).merge(
                venta_df[['id_venta', 'id_cliente']],
                on='id_venta',
                how='left'
            )
            
            ventas_totales_cliente = ventas_por_cliente.groupby('id_cliente')['total_linea'].sum().nlargest(10)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ventas_totales_cliente.plot(kind='line', marker='o', color='purple', ax=ax)
            ax.set_title('Total de Ventas por Cliente (Top 10)')
            ax.set_xlabel('ID Cliente')
            ax.set_ylabel('Total de Ventas ($)')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            graficos['ventas_por_cliente'] = fig
        
        # 8. CANTIDAD DE VENTAS POR CLIENTE
        if venta_df is not None:
            ventas_por_cliente_count = venta_df.groupby('id_cliente').size().nlargest(10)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ventas_por_cliente_count.plot(kind='bar', color='lightgreen', ax=ax)
            ax.set_title('Cantidad de Ventas por Cliente (Top 10)')
            ax.set_xlabel('ID Cliente')
            ax.set_ylabel('Cantidad de Ventas')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            graficos['ventas_cliente_cantidad'] = fig
            
    except Exception as e:
        st.error(f"Error generando gráficos: {e}")
    
    return graficos

# Cargar datos
dataframes = cargar_tablas()

# --- SECCIÓN: RESUMEN GENERAL ---
if seccion == " Resumen General":
    st.markdown('<h2 class="section-header"> Resumen General del Supermercado</h2>', unsafe_allow_html=True)
    
    if not dataframes:
        st.error("No se encontraron datos para mostrar. Verifica la carpeta de datos.")
        st.stop()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_tablas = len(dataframes)
        st.metric("Total de Tablas", total_tablas)
    
    with col2:
        total_registros = sum(len(df) for df in dataframes.values())
        st.metric("Total de Registros", f"{total_registros:,}")
    
    with col3:
        if 'factura_detalle' in dataframes:
            ventas_totales = dataframes['factura_detalle']['cantidad'].sum()
            st.metric("Productos Vendidos", f"{ventas_totales:,}")
    
    with col4:
        if 'cliente' in dataframes:
            total_clientes = len(dataframes['cliente'])
            st.metric("Total de Clientes", total_clientes)
    
    # Información de tablas
    st.markdown("###  Tablas Disponibles")
    
    for nombre, df in dataframes.items():
        with st.expander(f" {nombre} ({len(df)} registros)"):
            col_info, col_preview = st.columns([1, 2])
            
            with col_info:
                st.write(f"*Columnas:* {len(df.columns)}")
                st.write(f"*Registros:* {len(df)}")
                st.write("*Columnas:*")
                for col in df.columns:
                    st.write(f"  - {col}")
            
            with col_preview:
                st.dataframe(df.head(10), use_container_width=True)
                
                # Estadísticas básicas
                if df.select_dtypes(include=np.number).shape[1] > 0:
                    st.write("*Estadísticas:*")
                    st.dataframe(df.describe(), use_container_width=True)

# --- SECCIÓN: GRÁFICOS COMBINADOS ---
elif seccion == " Gráficos Combinados":
    st.markdown('<h2 class="section-header"> Gráficos Combinados</h2>', unsafe_allow_html=True)
    
    if not dataframes:
        st.error("No hay datos para generar gráficos")
        st.stop()
    
    # Generar gráficos
    with st.spinner("Generando gráficos..."):
        graficos = generar_graficos_combinados(dataframes)
    
    if not graficos:
        st.error("No se pudieron generar los gráficos. Verifica que las tablas necesarias estén disponibles.")
        st.stop()
    
    # Mostrar gráficos en una grid
    graficos_ordenados = [
        ('top10_productos', 'Top 10 Productos Más Vendidos'),
        ('ventas_por_rubro', 'Ventas por Rubro'),
        ('ventas_por_mes', 'Ventas por Mes'),
        ('ticket_promedio', 'Ticket Promedio'),
        ('facturas_mas_altas', 'Facturas Más Altas'),
        ('producto_mas_vendido', 'Producto Más Vendido'),
        ('ventas_por_cliente', 'Ventas por Cliente (Monto)'),
        ('ventas_cliente_cantidad', 'Ventas por Cliente (Cantidad)')
    ]
    
    for i in range(0, len(graficos_ordenados), 2):
        cols = st.columns(2)
        for j, (key, titulo) in enumerate(graficos_ordenados[i:i+2]):
            if key in graficos:
                with cols[j]:
                    st.pyplot(graficos[key])
                    st.caption(titulo)

# --- SECCIÓN: GESTIÓN DE DATOS ---
elif seccion == " Gestión de Datos":
    st.markdown('<h2 class="section-header"> Gestión de Datos</h2>', unsafe_allow_html=True)
    
    if not dataframes:
        st.error("No hay datos disponibles")
        st.stop()
    
    # Selector de tabla
    tabla_seleccionada = st.selectbox(
        "Selecciona una tabla para ver y gestionar:",
        list(dataframes.keys())
    )
    
    if tabla_seleccionada:
        df = dataframes[tabla_seleccionada]
        
        # Mostrar información de la tabla
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Registros", len(df))
        
        with col2:
            st.metric("Columnas", len(df.columns))
        
        with col3:
            memoria = df.memory_usage(deep=True).sum() / 1024  # KB
            st.metric("Memoria (KB)", f"{memoria:.2f}")
        
        # Vista de datos
        st.subheader(" Vista de Datos")
        
        # Filtros
        st.write("###  Filtros")
        col_filtro1, col_filtro2 = st.columns(2)
        
        df_filtrado = df.copy()
        
        with col_filtro1:
            columnas_numericas = df.select_dtypes(include=np.number).columns.tolist()
            if columnas_numericas:
                columna_filtro_num = st.selectbox("Filtrar por columna numérica:", columnas_numericas)
                if columna_filtro_num:
                    min_val = float(df[columna_filtro_num].min())
                    max_val = float(df[columna_filtro_num].max())
                    rango = st.slider(
                        f"Rango de {columna_filtro_num}",
                        min_val, max_val, (min_val, max_val)
                    )
                    df_filtrado = df_filtrado[
                        (df_filtrado[columna_filtro_num] >= rango[0]) & 
                        (df_filtrado[columna_filtro_num] <= rango[1])
                    ]
        
        with col_filtro2:
            columnas_categoricas = df.select_dtypes(include=['object']).columns.tolist()
            if columnas_categoricas:
                columna_filtro_cat = st.selectbox("Filtrar por columna categórica:", columnas_categoricas)
                if columna_filtro_cat:
                    opciones = df[columna_filtro_cat].unique().tolist()
                    seleccionados = st.multiselect(
                        f"Valores de {columna_filtro_cat}",
                        opciones,
                        default=opciones
                    )
                    if seleccionados:
                        df_filtrado = df_filtrado[df_filtrado[columna_filtro_cat].isin(seleccionados)]
        
        # Mostrar datos filtrados
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Estadísticas
        st.subheader(" Estadísticas")
        
        col_stats1, col_stats2 = st.columns(2)
        
        with col_stats1:
            st.write("*Resumen Numérico:*")
            if df_filtrado.select_dtypes(include=np.number).shape[1] > 0:
                st.dataframe(df_filtrado.describe(), use_container_width=True)
            else:
                st.info("No hay columnas numéricas en esta tabla")
        
        with col_stats2:
            st.write("*Información de Datos:*")
            buffer = io.StringIO()
            df_filtrado.info(buf=buffer)
            info_text = buffer.getvalue()
            st.text_area("Info:", info_text, height=200, disabled=True)

# --- SECCIÓN: DESCARGAS ---
elif seccion == " Descargas":
    st.markdown('<h2 class="section-header">📥 Descarga de Datos</h2>', unsafe_allow_html=True)
    
    if not dataframes:
        st.error("No hay datos disponibles para descargar")
        st.stop()
    
    # Descargas individuales por tabla
    st.subheader(" Descargas Individuales por Tabla")
    
    tabla_descarga = st.selectbox(
        "Selecciona una tabla para descargar:",
        list(dataframes.keys())
    )
    
    if tabla_descarga:
        df = dataframes[tabla_descarga]
        
        col_csv, col_json, col_excel = st.columns(3)
        
        with col_csv:
            csv_data = convertir_df_csv(df)
            st.download_button(
                label=" Descargar CSV",
                data=csv_data,
                file_name=f"{tabla_descarga}.csv",
                mime="text/csv"
            )
        
        with col_json:
            json_data = convertir_df_json(df)
            st.download_button(
                label=" Descargar JSON",
                data=json_data,
                file_name=f"{tabla_descarga}.json",
                mime="application/json"
            )
        
        with col_excel:
            excel_data = convertir_df_excel(df)
            st.download_button(
                label=" Descargar Excel",
                data=excel_data,
                file_name=f"{tabla_descarga}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    # Descargas combinadas
    st.subheader(" Descargas Combinadas")
    
    col_comb1, col_comb2 = st.columns(2)
    
    with col_comb1:
        # Excel combinado
        if st.button(" Generar Excel Combinado"):
            with st.spinner("Generando Excel combinado..."):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    for nombre, df in dataframes.items():
                        df.to_excel(writer, sheet_name=nombre[:31], index=False)
                
                excel_data = output.getvalue()
                
                st.download_button(
                    label=" Descargar Excel Combinado",
                    data=excel_data,
                    file_name="datos_combinados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col_comb2:
        # JSON combinado
        if st.button(" Generar JSON Combinado"):
            with st.spinner("Generando JSON combinado..."):
                datos_combinados = {}
                for nombre, df in dataframes.items():
                    datos_combinados[nombre] = df.to_dict('records')
                
                json_data = json.dumps(datos_combinados, indent=4, ensure_ascii=False).encode('utf-8')
                
                st.download_button(
                    label=" Descargar JSON Combinado",
                    data=json_data,
                    file_name="datos_combinados.json",
                    mime="application/json"
                )
    
    # Información del dataset
    st.subheader(" Información del Dataset Completo")
    
    info_col1, info_col2, info_col3 = st.columns(3)
    
    with info_col1:
        st.metric("Total de Tablas", len(dataframes))
    
    with info_col2:
        total_registros = sum(len(df) for df in dataframes.values())
        st.metric("Total de Registros", f"{total_registros:,}")
    
    with info_col3:
        total_columnas = sum(len(df.columns) for df in dataframes.values())
        st.metric("Total de Columnas", total_columnas)
    
    # Lista de tablas disponibles
    st.write("###  Tablas Disponibles para Descarga")
    for nombre, df in dataframes.items():
        st.write(f"*{nombre}* - {len(df)} registros, {len(df.columns)} columnas")

# Footer
st.markdown("---")
st.markdown(
    "*Dashboard Supermercado* | Desarrollado con Streamlit | "
    f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)


