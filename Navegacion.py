#----------------------------------------------------------------------
#Página web para CECMI
#Archivo para la navegación entre páginas
#Por: Andrea Solis Garza, 593315
#-----------------------------------------------------------------------

#Importar librerias
import streamlit as st

#Listar páginas
pages = [
    st.Page("CECMI_app.py", title="Página Principal"),
    st.Page("Mapa_muestras.py", title="Mapa de Muestras")
]

#incluir navegación
pg = st.navigation(pages, position="sidebar", expanded=False)
pg.run()