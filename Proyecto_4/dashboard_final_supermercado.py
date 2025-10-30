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
from matplotlib.backends.backend_pdf import PdfPages

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
    ["📊 Resumen General", "📈 Gráficos Combinados", "🗂️ Gestión de Datos", "📥 Descargas", "📄 Informe Final"]
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
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
            
            # Gráfico de barras
            ax1.bar(range(len(productos_vendidos_con_nombre)), productos_vendidos_con_nombre['cantidad'], color='#2e86ab')
            ax1.set_title('Top 10 Productos Más Vendidos', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Productos', fontsize=12)
            ax1.set_ylabel('Cantidad Vendida', fontsize=12)
            ax1.set_xticks(range(len(productos_vendidos_con_nombre)))
            ax1.set_xticklabels(productos_vendidos_con_nombre['nombre_producto'], rotation=45, ha='right')
            ax1.grid(axis='y', alpha=0.3)
            
            # Gráfico de torta
            ax2.pie(productos_vendidos_con_nombre['cantidad'], labels=productos_vendidos_con_nombre['nombre_producto'], 
                   autopct='%1.1f%%', startangle=90)
            ax2.set_title('Distribución Top 10 Productos', fontsize=14, fontweight='bold')
            
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
            
            fig, ax = plt.subplots(figsize=(14, 7))
            ventas_por_rubro.plot(kind='bar', color='skyblue', ax=ax)
            ax.set_title('Ventas Totales por Rubro', fontsize=14, fontweight='bold')
            ax.set_xlabel('Rubro', fontsize=12)
            ax.set_ylabel('Cantidad Vendida', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            graficos['ventas_por_rubro'] = fig
        
        # 3. VENTAS POR MES
        if factura_enunciado_df is not None:
            factura_enunciado_df['fecha'] = pd.to_datetime(factura_enunciado_df['fecha'])
            ventas_por_mes = factura_enunciado_df.groupby(factura_enunciado_df['fecha'].dt.to_period('M')).size()
            
            fig, ax = plt.subplots(figsize=(14, 7))
            ventas_por_mes.plot(kind='line', marker='o', color='green', linewidth=2, markersize=8, ax=ax)
            ax.set_title('Ventas por Mes', fontsize=14, fontweight='bold')
            ax.set_xlabel('Mes', fontsize=12)
            ax.set_ylabel('Cantidad de Ventas', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
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
            
            fig, ax = plt.subplots(figsize=(14, 7))
            ticket_promedio.plot(kind='bar', color='orange', ax=ax)
            ax.set_title('Ticket Promedio por Cliente (Top 10)', fontsize=14, fontweight='bold')
            ax.set_xlabel('ID Cliente', fontsize=12)
            ax.set_ylabel('Ticket Promedio ($)', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            graficos['ticket_promedio'] = fig
        
        # 5. FACTURAS MÁS ALTAS
        if factura_detalle_df is not None:
            factura_detalle_df['total_linea'] = factura_detalle_df['cantidad'] * factura_detalle_df['precio_unitario']
            total_por_factura = factura_detalle_df.groupby('id_factura')['total_linea'].sum().nlargest(10)
            
            fig, ax = plt.subplots(figsize=(14, 7))
            total_por_factura.plot(kind='bar', color='red', ax=ax)
            ax.set_title('Top 10 Facturas Más Altas', fontsize=14, fontweight='bold')
            ax.set_xlabel('ID Factura', fontsize=12)
            ax.set_ylabel('Monto Total ($)', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(axis='y', alpha=0.3)
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
            
            fig, ax = plt.subplots(figsize=(14, 7))
            ax.bar(producto_mas_vendido_con_nombre['nombre_producto'], producto_mas_vendido_con_nombre['cantidad'], 
                  color='#1f77b4')
            ax.set_title('Top 5 Productos Más Vendidos', fontsize=14, fontweight='bold')
            ax.set_xlabel('Producto', fontsize=12)
            ax.set_ylabel('Cantidad Vendida', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            graficos['producto_mas_vendido'] = fig
        
        # 7. VENTAS POR CLIENTE (CAMBIO A BARRAS)
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
            
            fig, ax = plt.subplots(figsize=(14, 7))
            ventas_totales_cliente.plot(kind='bar', color='purple', ax=ax)
            ax.set_title('Total de Ventas por Cliente (Top 10)', fontsize=14, fontweight='bold')
            ax.set_xlabel('ID Cliente', fontsize=12)
            ax.set_ylabel('Total de Ventas ($)', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            graficos['ventas_por_cliente'] = fig
        
        # 8. CANTIDAD DE VENTAS POR CLIENTE
        if venta_df is not None:
            ventas_por_cliente_count = venta_df.groupby('id_cliente').size().nlargest(10)
            
            fig, ax = plt.subplots(figsize=(14, 7))
            ventas_por_cliente_count.plot(kind='bar', color='lightgreen', ax=ax)
            ax.set_title('Cantidad de Ventas por Cliente (Top 10)', fontsize=14, fontweight='bold')
            ax.set_xlabel('ID Cliente', fontsize=12)
            ax.set_ylabel('Cantidad de Ventas', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            graficos['ventas_cliente_cantidad'] = fig
        
        # 9. VENTAS MENSUALES (NUEVO)
        if factura_enunciado_df is not None:
            factura_enunciado_df['fecha'] = pd.to_datetime(factura_enunciado_df['fecha'])
            
            # Crear DataFrame con detalles
            ventas_detalle = factura_detalle_df.merge(
                factura_enunciado_df[['id_factura', 'fecha', 'id_venta']],
                on='id_factura',
                how='left'
            )
            ventas_detalle['total_linea'] = ventas_detalle['cantidad'] * ventas_detalle['precio_unitario']
            
            # Ventas mensuales por mes del año
            ventas_detalle['mes'] = ventas_detalle['fecha'].dt.month
            ventas_mensuales = ventas_detalle.groupby('mes')['total_linea'].sum()
            
            # Nombres de meses
            meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            
            fig, ax = plt.subplots(figsize=(14, 7))
            ax.plot(ventas_mensuales.index, ventas_mensuales.values, marker='o', color='#FF6B6B', linewidth=2.5, markersize=8)
            ax.set_title('Ventas Mensuales', fontsize=14, fontweight='bold')
            ax.set_xlabel('Mes', fontsize=12)
            ax.set_ylabel('Total de Ventas ($)', fontsize=12)
            ax.set_xticks(ventas_mensuales.index)
            ax.set_xticklabels([meses_nombres[i-1] for i in ventas_mensuales.index], rotation=45)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            graficos['ventas_mensuales'] = fig
        
        # 10. VENTAS SEMANALES (NUEVO)
        if factura_enunciado_df is not None:
            # Ventas por día de la semana
            ventas_detalle['dia_semana'] = ventas_detalle['fecha'].dt.dayofweek
            ventas_semanales = ventas_detalle.groupby('dia_semana')['total_linea'].sum()
            
            # Nombres de días
            dias_nombres = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            
            fig, ax = plt.subplots(figsize=(14, 7))
            ax.plot(ventas_semanales.index, ventas_semanales.values, marker='s', color='#4ECDC4', linewidth=2.5, markersize=8)
            ax.set_title('Ventas Semanales (Por Día de la Semana)', fontsize=14, fontweight='bold')
            ax.set_xlabel('Día de la Semana', fontsize=12)
            ax.set_ylabel('Total de Ventas ($)', fontsize=12)
            ax.set_xticks(ventas_semanales.index)
            ax.set_xticklabels([dias_nombres[i] for i in ventas_semanales.index], rotation=45)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            graficos['ventas_semanales'] = fig
        
        # 11. VENTAS ANUALES (NUEVO)
        if factura_enunciado_df is not None:
            ventas_detalle['año'] = ventas_detalle['fecha'].dt.year
            ventas_anuales = ventas_detalle.groupby('año')['total_linea'].sum().sort_index()
            
            fig, ax = plt.subplots(figsize=(14, 7))
            ax.plot(ventas_anuales.index, ventas_anuales.values, marker='D', color='#FFD93D', linewidth=3, markersize=10)
            ax.set_title('Ventas Anuales', fontsize=14, fontweight='bold')
            ax.set_xlabel('Año', fontsize=12)
            ax.set_ylabel('Total de Ventas ($)', fontsize=12)
            ax.set_xticks(ventas_anuales.index)
            ax.set_xticklabels(ventas_anuales.index.astype(int), rotation=0)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            graficos['ventas_anuales'] = fig
            
    except Exception as e:
        st.error(f"Error generando gráficos: {e}")
    
    return graficos

def generar_informe_excel(dataframes, graficos):
    """Genera un archivo Excel con datos y gráficos"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Escribir resumen general
        resumen_data = {
            'Métrica': ['Total de Tablas', 'Total de Registros', 'Total de Clientes', 'Productos Vendidos'],
            'Valor': [
                len(dataframes),
                sum(len(df) for df in dataframes.values()),
                len(dataframes.get('cliente', pd.DataFrame())),
                dataframes.get('factura_detalle', pd.DataFrame()).get('cantidad', pd.Series()).sum() if 'factura_detalle' in dataframes else 0
            ]
        }
        pd.DataFrame(resumen_data).to_excel(writer, sheet_name='Resumen', index=False)
        
        # Escribir cada tabla
        for nombre, df in dataframes.items():
            sheet_name = nombre[:31]  # Excel limita a 31 caracteres
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    return output.getvalue()

def generar_informe_pdf(dataframes, graficos):
    """Genera un archivo PDF con gráficos e información"""
    output = io.BytesIO()
    
    try:
        with PdfPages(output) as pdf:
            # Página de portada
            fig = plt.figure(figsize=(11, 8.5))
            fig.text(0.5, 0.6, 'Informe de Análisis', ha='center', fontsize=28, fontweight='bold')
            fig.text(0.5, 0.5, 'Dashboard Supermercado', ha='center', fontsize=20)
            fig.text(0.5, 0.4, f'Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ha='center', fontsize=12)
            
            # Métricas
            productos_vendidos = 0
            if 'factura_detalle' in dataframes and 'cantidad' in dataframes['factura_detalle'].columns:
                productos_vendidos = int(dataframes['factura_detalle']['cantidad'].sum())
            
            metrics_text = f"""
            Total de Tablas: {len(dataframes)}
            Total de Registros: {sum(len(df) for df in dataframes.values()):,}
            Total de Clientes: {len(dataframes.get('cliente', pd.DataFrame()))}
            Productos Vendidos: {productos_vendidos:,}
            """
            fig.text(0.5, 0.25, metrics_text, ha='center', fontsize=12, family='monospace')
            plt.axis('off')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            
            # Agregar cada gráfico en páginas separadas
            for nombre, grafico in graficos.items():
                try:
                    pdf.savefig(grafico, bbox_inches='tight')
                except Exception as e:
                    print(f"Error guardando gráfico {nombre}: {e}")
        
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        print(f"Error general en PDF: {e}")
        raise

# Cargar datos
dataframes = cargar_tablas()

# --- SECCIÓN: RESUMEN GENERAL ---
if seccion == "📊 Resumen General":
    st.markdown('<h2 class="section-header">📊 Resumen General del Supermercado</h2>', unsafe_allow_html=True)
    
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
    st.markdown("### 📋 Tablas Disponibles")
    
    for nombre, df in dataframes.items():
        with st.expander(f"📊 {nombre} ({len(df)} registros)"):
            col_info, col_preview = st.columns([1, 2])
            
            with col_info:
                st.write(f"**Columnas:** {len(df.columns)}")
                st.write(f"**Registros:** {len(df)}")
                st.write("**Columnas:**")
                for col in df.columns:
                    st.write(f"  - {col}")
            
            with col_preview:
                st.dataframe(df.head(10), use_container_width=True)
                
                # Estadísticas básicas
                if df.select_dtypes(include=np.number).shape[1] > 0:
                    st.write("**Estadísticas:**")
                    st.dataframe(df.describe(), use_container_width=True)

# --- SECCIÓN: GRÁFICOS COMBINADOS ---
elif seccion == "📈 Gráficos Combinados":
    st.markdown('<h2 class="section-header">📈 Gráficos Combinados</h2>', unsafe_allow_html=True)
    
    if not dataframes:
        st.error("No hay datos para generar gráficos")
        st.stop()
    
    # Generar gráficos
    with st.spinner("Generando gráficos..."):
        graficos = generar_graficos_combinados(dataframes)
    
    if not graficos:
        st.error("No se pudieron generar los gráficos. Verifica que las tablas necesarias estén disponibles.")
        st.stop()
    
    # Mostrar gráficos uno por uno para mejor visualización
    if 'top10_productos' in graficos:
        st.pyplot(graficos['top10_productos'], use_container_width=True)
    
    if 'ventas_por_rubro' in graficos:
        st.pyplot(graficos['ventas_por_rubro'], use_container_width=True)
    
    if 'ventas_por_mes' in graficos:
        st.pyplot(graficos['ventas_por_mes'], use_container_width=True)
    
    if 'ticket_promedio' in graficos:
        st.pyplot(graficos['ticket_promedio'], use_container_width=True)
    
    if 'facturas_mas_altas' in graficos:
        st.pyplot(graficos['facturas_mas_altas'], use_container_width=True)
    
    if 'producto_mas_vendido' in graficos:
        st.pyplot(graficos['producto_mas_vendido'], use_container_width=True)
    
    if 'ventas_por_cliente' in graficos:
        st.pyplot(graficos['ventas_por_cliente'], use_container_width=True)
    
    if 'ventas_cliente_cantidad' in graficos:
        st.pyplot(graficos['ventas_cliente_cantidad'], use_container_width=True)
    
    # NUEVOS GRÁFICOS DE TENDENCIAS
    st.markdown("---")
    st.subheader("📅 Análisis de Tendencias Temporales")
    
    if 'ventas_mensuales' in graficos:
        st.pyplot(graficos['ventas_mensuales'], use_container_width=True)
    
    if 'ventas_semanales' in graficos:
        st.pyplot(graficos['ventas_semanales'], use_container_width=True)
    
    if 'ventas_anuales' in graficos:
        st.pyplot(graficos['ventas_anuales'], use_container_width=True)

# --- SECCIÓN: GESTIÓN DE DATOS ---
elif seccion == "🗂️ Gestión de Datos":
    st.markdown('<h2 class="section-header">🗂️ Gestión de Datos</h2>', unsafe_allow_html=True)
    
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
        st.subheader("📊 Vista de Datos")
        
        # Filtros
        st.write("### 🔍 Filtros")
        col_filtro1, col_filtro2 = st.columns(2)
        
        df_filtrado = df.copy()
        
        # EXCLUIR COLUMNAS QUE CONTENGAN 'ID' O 'INDEX'
        columnas_excluidas = [col for col in df_filtrado.columns if 'id' in col.lower() or 'index' in col.lower()]
        df_visualizacion = df_filtrado.drop(columns=columnas_excluidas, errors='ignore')
        
        with col_filtro1:
            columnas_numericas = df.select_dtypes(include=np.number).columns.tolist()
            # Filtrar columnas numéricas excluyendo IDs
            columnas_numericas = [col for col in columnas_numericas if col not in columnas_excluidas]
            
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
                    df_visualizacion = df_filtrado.drop(columns=columnas_excluidas, errors='ignore')
        
        with col_filtro2:
            columnas_categoricas = df.select_dtypes(include=['object']).columns.tolist()
            # Filtrar columnas categóricas excluyendo IDs
            columnas_categoricas = [col for col in columnas_categoricas if col not in columnas_excluidas]
            
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
                        df_visualizacion = df_filtrado.drop(columns=columnas_excluidas, errors='ignore')
        
        # Mostrar datos filtrados SIN COLUMNAS DE ID O INDEX
        st.dataframe(df_visualizacion, use_container_width=True)
        
        # Estadísticas
        st.subheader("📊 Estadísticas")
        
        col_stats1, col_stats2 = st.columns(2)
        
        with col_stats1:
            st.write("**Resumen Numérico:**")
            if df_filtrado.select_dtypes(include=np.number).shape[1] > 0:
                # Mostrar estadísticas sin columnas de ID
                df_stats = df_filtrado.select_dtypes(include=np.number).drop(columns=columnas_excluidas, errors='ignore')
                if len(df_stats.columns) > 0:
                    st.dataframe(df_stats.describe(), use_container_width=True)
                else:
                    st.info("No hay columnas numéricas (excepto IDs) en esta tabla")
            else:
                st.info("No hay columnas numéricas en esta tabla")
        
        with col_stats2:
            st.write("**Información de Datos:**")
            buffer = io.StringIO()
            df_filtrado.info(buf=buffer)
            info_text = buffer.getvalue()
            st.text_area("Info:", info_text, height=200, disabled=True)

# --- SECCIÓN: DESCARGAS ---
elif seccion == "📥 Descargas":
    st.markdown('<h2 class="section-header">📥 Descarga de Datos</h2>', unsafe_allow_html=True)
    
    if not dataframes:
        st.error("No hay datos disponibles para descargar")
        st.stop()
    
    # Descargas individuales por tabla
    st.subheader("📊 Descargas Individuales por Tabla")
    
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
                label="📄 Descargar CSV",
                data=csv_data,
                file_name=f"{tabla_descarga}.csv",
                mime="text/csv"
            )
        
        with col_json:
            json_data = convertir_df_json(df)
            st.download_button(
                label="📋 Descargar JSON",
                data=json_data,
                file_name=f"{tabla_descarga}.json",
                mime="application/json"
            )
        
        with col_excel:
            excel_data = convertir_df_excel(df)
            st.download_button(
                label="📊 Descargar Excel",
                data=excel_data,
                file_name=f"{tabla_descarga}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    # Descargas combinadas
    st.subheader("📦 Descargas Combinadas")
    
    col_comb1, col_comb2 = st.columns(2)
    
    with col_comb1:
        # Excel combinado
        if st.button("📊 Generar Excel Combinado"):
            with st.spinner("Generando Excel combinado..."):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    for nombre, df in dataframes.items():
                        df.to_excel(writer, sheet_name=nombre[:31], index=False)
                
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📥 Descargar Excel Combinado",
                    data=excel_data,
                    file_name="datos_combinados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col_comb2:
        # JSON combinado
        if st.button("📋 Generar JSON Combinado"):
            with st.spinner("Generando JSON combinado..."):
                datos_combinados = {}
                for nombre, df in dataframes.items():
                    datos_combinados[nombre] = df.to_dict('records')
                
                json_data = json.dumps(datos_combinados, indent=4, ensure_ascii=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Descargar JSON Combinado",
                    data=json_data,
                    file_name="datos_combinados.json",
                    mime="application/json"
                )
    
    # Información del dataset
    st.subheader("📈 Información del Dataset Completo")
    
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
    st.write("### 📋 Tablas Disponibles para Descarga")
    for nombre, df in dataframes.items():
        st.write(f"**{nombre}** - {len(df)} registros, {len(df.columns)} columnas")

# --- SECCIÓN: INFORME FINAL ---
elif seccion == "📄 Informe Final":
    st.markdown('<h2 class="section-header">📄 Informe Final</h2>', unsafe_allow_html=True)
    
    if not dataframes:
        st.error("No hay datos disponibles para generar el informe")
        st.stop()
    
    st.markdown("""
    ### 📊 Informe Ejecutivo - Dashboard Supermercado
    
    Este informe contiene un análisis completo de los datos del supermercado, incluyendo métricas clave,
    visualizaciones y datos detallados. Puede descargar el informe completo en formato Excel o PDF.
    """)
    
    # Generar gráficos para el informe
    with st.spinner("Generando análisis..."):
        graficos = generar_graficos_combinados(dataframes)
    
    # Sección de métricas principales
    st.markdown("---")
    st.subheader("📈 Métricas Principales")
    
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
        else:
            st.metric("Productos Vendidos", "N/A")
    
    with col4:
        if 'cliente' in dataframes:
            total_clientes = len(dataframes['cliente'])
            st.metric("Total de Clientes", total_clientes)
        else:
            st.metric("Total de Clientes", "N/A")
    
    # Mostrar gráficos en el informe
    st.markdown("---")
    st.subheader("📊 Visualizaciones")
    
    # Crear tabs para organizar los gráficos
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Productos y Ventas", "💰 Análisis Financiero", "👥 Clientes", "📅 Tendencias"])
    
    with tab1:
        if 'top10_productos' in graficos:
            fig_copy = graficos['top10_productos']
            st.pyplot(fig_copy, use_container_width=True)
        
        if 'producto_mas_vendido' in graficos:
            fig_copy = graficos['producto_mas_vendido']
            st.pyplot(fig_copy, use_container_width=True)
        
        if 'ventas_por_rubro' in graficos:
            fig_copy = graficos['ventas_por_rubro']
            st.pyplot(fig_copy, use_container_width=True)
    
    with tab2:
        if 'facturas_mas_altas' in graficos:
            fig_copy = graficos['facturas_mas_altas']
            st.pyplot(fig_copy, use_container_width=True)
        
        if 'ticket_promedio' in graficos:
            fig_copy = graficos['ticket_promedio']
            st.pyplot(fig_copy, use_container_width=True)
    
    with tab3:
        if 'ventas_por_cliente' in graficos:
            fig_copy = graficos['ventas_por_cliente']
            st.pyplot(fig_copy, use_container_width=True)
        
        if 'ventas_cliente_cantidad' in graficos:
            fig_copy = graficos['ventas_cliente_cantidad']
            st.pyplot(fig_copy, use_container_width=True)
    
    with tab4:
        if 'ventas_por_mes' in graficos:
            fig_copy = graficos['ventas_por_mes']
            st.pyplot(fig_copy, use_container_width=True)
        
        if 'ventas_mensuales' in graficos:
            fig_copy = graficos['ventas_mensuales']
            st.pyplot(fig_copy, use_container_width=True)
        
        if 'ventas_semanales' in graficos:
            fig_copy = graficos['ventas_semanales']
            st.pyplot(fig_copy, use_container_width=True)
        
        if 'ventas_anuales' in graficos:
            fig_copy = graficos['ventas_anuales']
            st.pyplot(fig_copy, use_container_width=True)
    
    # Sección de descargas del informe
    st.markdown("---")
    st.subheader("📥 Descargar Informe Completo")
    
    col_download1, col_download2 = st.columns(2)
    
    with col_download1:
        if st.button("📊 Generar Informe Excel", type="primary", use_container_width=True):
            with st.spinner("Generando informe Excel..."):
                try:
                    excel_data = generar_informe_excel(dataframes, graficos)
                    st.download_button(
                        label="📥 Descargar Informe Excel",
                        data=excel_data,
                        file_name=f"informe_supermercado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    st.success("✅ Informe Excel generado correctamente")
                except Exception as e:
                    st.error(f"❌ Error generando informe Excel: {e}")
    
    with col_download2:
        if st.button("📄 Generar Informe PDF", type="primary", use_container_width=True):
            with st.spinner("Generando informe PDF..."):
                try:
                    pdf_data = generar_informe_pdf(dataframes, graficos)
                    st.download_button(
                        label="📥 Descargar Informe PDF",
                        data=pdf_data,
                        file_name=f"informe_supermercado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("✅ Informe PDF generado correctamente")
                except Exception as e:
                    st.error(f"❌ Error generando informe PDF: {e}")
    
    # Resumen de tablas incluidas
    st.markdown("---")
    st.subheader("📋 Tablas Incluidas en el Informe")
    
    tabla_info = []
    for nombre, df in dataframes.items():
        tabla_info.append({
            'Tabla': nombre,
            'Registros': len(df),
            'Columnas': len(df.columns)
        })
    
    df_info = pd.DataFrame(tabla_info)
    st.dataframe(df_info, use_container_width=True, hide_index=True)
    
    # Nota informativa
    st.info("""
    **📌 Nota:** El informe Excel incluye todas las tablas de datos en hojas separadas más una hoja de resumen.
    El informe PDF incluye los gráficos de análisis y métricas principales en formato profesional.
    """)

# Footer
st.markdown("---")
st.markdown(
    "**Dashboard Supermercado** | Desarrollado con Streamlit | "
    f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)