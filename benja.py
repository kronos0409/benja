import streamlit as st
import pandas as pd
import requests as rq
import matplotlib.pyplot as plt
from io import BytesIO
import time
# URL de la API
API_URL = "https://datos.gob.cl/dataset/3bf4cf7c-f638-4735-9a01-f65faae4beca/resource/2c44d782-3365-44e3-aefb-2c8b8363a1bc/download/establecimientos_20241126.csv"

# Diccionario para traducir códigos de región
REGIONES = {
    1: "Tarapacá", 2: "Antofagasta", 3: "Atacama", 4: "Coquimbo",
    5: "Valparaíso", 6: "O'Higgins", 7: "Maule", 8: "Biobío",
    9: "La Araucanía", 10: "Los Lagos", 11: "Aysén", 12: "Magallanes",
    13: "Metropolitana", 14: "Los Ríos", 15: "Arica y Parinacota", 16: "Ñuble"
}

# Cargar datos desde la API
@st.cache_data
def cargar_datos(url):
    try:
        respuesta = rq.get(url)
        respuesta.raise_for_status()  # Lanza un error si la respuesta no es exitosa
        datos = pd.read_csv(BytesIO(respuesta.content), sep=";")
        return datos
    except rq.exceptions.RequestException as e:
        st.error(f"Hubo un error al intentar cargar los datos. Error: {e}")
        return pd.DataFrame()  # Retornamos un DataFrame vacío si falla
    except Exception as e:
        st.error(f"Error inesperado: {e}")
        return pd.DataFrame()

# Procesar datos: traducir regiones y filtrar columnas importantes
def procesar_datos(datos):
    if datos is not None:
        columnas_necesarias = [
            "EstablecimientoGlosa", "RegionCodigo", "RegionGlosa",
            "TipoEstablecimientoGlosa", "DependenciaAdministrativa",
            "ComunaGlosa", "EstadoFuncionamiento"
        ]
        datos = datos[columnas_necesarias].copy()
        datos["RegionNombre"] = datos["RegionCodigo"].map(REGIONES)
        return datos
    else:
        return None

# Mostrar datos filtrados
def mostrar_datos(datos):
    st.subheader("Filtrar Establecimientos")
    opcion = st.radio("Filtrar por", ["Región", "Comuna", "Todo el País"])
    datos_filtrados=pd.DataFrame()
    if opcion == "Región":
        region = st.selectbox("Selecciona una región", REGIONES.values())
        region_codigo = list(REGIONES.keys())[list(REGIONES.values()).index(region)]
        datos_filtrados = datos[datos["RegionCodigo"] == region_codigo]
    elif opcion == "Comuna":
        comuna = st.selectbox("Escribe el nombre de una comuna",options=list(datos["ComunaGlosa"].unique()),index=None)
        if comuna != None and comuna!="":
            datos_filtrados = datos[datos["ComunaGlosa"].str.contains(comuna, case=False, na=False)]
    else:
        datos_filtrados = datos
    if not datos_filtrados.empty:
        st.dataframe(datos_filtrados)
    return datos_filtrados

# Gráficos: Distribución por tipo de establecimiento y dependencia
def mostrar_graficos(datos):
    st.subheader("Visualización de Datos")
    tipo_grafico = st.selectbox("Selecciona un gráfico", ["Distribución por Tipo", "Proporción por Dependencia"])
    
    if tipo_grafico == "Distribución por Tipo":
        plt.clf()
        datos["TipoEstablecimientoGlosa"].value_counts().plot(kind="bar", color="skyblue")
        plt.title("Distribución por Tipo de Establecimiento")
        plt.xlabel("Tipo de Establecimiento")
        plt.ylabel("Cantidad")
        st.pyplot(plt)
    elif tipo_grafico == "Proporción por Dependencia":
        plt.clf()
        datos["DependenciaAdministrativa"].value_counts(normalize=True).plot(kind="pie", autopct='%1.1f%%')
        plt.title("Proporción por Dependencia Administrativa")
        st.pyplot(plt)

# Gráfico de torta: Establecimientos en uso vs cerrados
def grafico_estado(datos):
    st.subheader("Estado de Funcionamiento")
    if "EstadoFuncionamiento" in datos.columns:
        plt.clf()
        datos["EstadoFuncionamiento"].value_counts().plot(kind="pie", autopct='%1.1f%%', colors=["limegreen", "gray"])
        plt.title("Establecimientos en Uso vs Cerrados")
        st.pyplot(plt)

# Exportar datos a CSV
def exportar_datos(datos):
    st.subheader("Exportar Datos")
    csv = datos.to_csv(index=False)
    st.download_button(
        label="Descargar datos como CSV",
        data=csv,
        file_name="establecimientos_salud.csv",
        mime="text/csv"
    )

# Función principal
def main():
    st.write("<h1 style='text-align:center';>Explorador de Establecimientos de Salud en Chile</h1>",unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center';>Visualiza y analiza los datos de establecimientos de salud en Chile proporcionados por el MINSAL.</h4>",unsafe_allow_html=True)
    c1,c2,c3 = st.columns([2,1.5,1.5])
    # Cargar y procesar datos
    with st.spinner("Cargando datos desde la API..."):
        datos = cargar_datos(API_URL)
        if datos is not None:
            datos = procesar_datos(datos)
            if datos is not None:
                with c1:
                # Mostrar datos
                    datos_filtrados = mostrar_datos(datos)

                # Mostrar gráficos
                if datos_filtrados is not None and not datos_filtrados.empty:
                    with c2:
                        mostrar_graficos(datos_filtrados)
                    with c3:
                        for i in range(5):
                            st.write('')
                        grafico_estado(datos_filtrados)

                # Exportar datos
                with c1:
                    exportar_datos(datos)
        else:
            st.error("No se pudieron cargar los datos.")

main()
