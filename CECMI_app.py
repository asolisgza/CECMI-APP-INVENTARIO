#-----------------------------------------------------------------------
#Página Web de CECMI para el registro digital de elementos en congelador de -80°C
#Autora: Andrea Solis, 593315
#------------------------------------------------------------------------

#Importar librerias--------------------------------------------------------
import streamlit as st
import pandas as pd
import Mapa_muestras as MM

#Funciones------------------------------------------------------------------

#Funcion para asignar el color de fondo de tabla
def color_por_palabra(val):
    if val == "NOM":
        return "background-color: #0A3463; color: #FFFFFF"  # Verde claro + texto verde oscuro
    return ""  # Sin cambios para las demás palabras


#Dar diseño a la página----------------------------------------------------

#Color de fondo principal, de la barra lateral, texto y botones
#Código en CSS
st.html("""
    <style>
    /* Fondo principal de la app */
    .stApp {
        background-color: #F5FEFD;
    }

    /* Cambiar el fondo de la barra lateral */
    [data-testid="stSidebar"] {
        background-color: #16425b;
    }
    
    /* Cambiar el color del texto dentro de la barra lateral */
    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }
    
    /*Cambiar el color de los contenedores*/
    .st-key-my-temperature {
        background-color: #DEF7FF;
        border-radius: 12px;
        padding: 16px;
    }

    .st-key-my-samples {
        background-color: #DEF7FF;
        border-radius: 12px;
        padding: 16px;
    }

    .st-key-my-free-space {
        background-color: #DEF7FF;
        border-radius: 12px;
        padding: 16px;
    }    

    .st-key-my-extsamp {
            background-color: #FFFFFF;
            border-radius: 12px;
            padding: 16px;
        }
    
    .st-key-my-add_ext {
                background-color: #FFFFFF;
                border-radius: 12px;
                padding: 16px;
            }

    /* Estilizar los botones */
    div.stButton > button {
        background-color: #0284c7;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
    
    /* Efecto al pasar el cursor sobre un botón */
    div.stButton > button:hover {
        background-color: #0369a1;
        color: white;
    }
    </style>
""")

#Contenido de la página ------------------------------------------------

#Encabezado
st.markdown("<h1 style='color: #191970;'>Inventario Digital de Congelador CECMI</h1>", unsafe_allow_html=True)
st.write("Gestión de muestras y ubicación")

#Resumen
st.header("Datos principales")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(key="my-temperature", height = 125):
        icon_col, text_col = st.columns(2)

        with icon_col:
            st.image("thermometer.svg", width = 50)

        with text_col:
            st.metric("Temperatura", "-80 °C")

with col2:
    with st.container(key="my-samples", height = 125):
        icon_col, text_col = st.columns(2)
        
        with icon_col:
            st.image("real_sample.svg", width = 100)
        
        with text_col:
            st.metric("Muestras almacenadas", MM.num_samples_cont1)

with col3:
    with st.container(key="my-free-space", height = 125):
        icon_col, text_col = st.columns(2)
                
        with icon_col:
            st.image("sample.svg", width = 100)
        
        with text_col:
            st.metric("Espacio libre", f"{int(MM.por_free_space)}%")

#Contenido principal

extsamp, addsamp = st.columns(2)

with extsamp:
    with st.container(key="my-extsamp"):
        st.subheader("Resumen de Muestras")
        with st.expander("**Caja Criogénica 1**"):
            for (row, col), info in st.session_state["sample"].items():
                st.write(f"Ubicación: {row}-{col} | ID: {info['id']} | Fecha de ingreso: {info['fecha']}")
        
        

with addsamp:
    with st.container(key="my-add_ext"):
        st.subheader("CONTENIDO")
        

with st.expander("Ver recomendaciones de seguridad ISBER"):
    st.write("Mantener la puerta abierta por menos de 45 segundos.")


