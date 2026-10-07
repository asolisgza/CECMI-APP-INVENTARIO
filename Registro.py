#----------------------------------------------------------------------
#Página web para CECMI
#Archivo para registro de los movimientos
#Por: Andrea Solis Garza, 593315
#-----------------------------------------------------------------------

import pandas as pd
import streamlit as st

from movements import clear_movements, load_movements

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
        min-height: 150px;
    }

    .st-key-my-samples {
        background-color: #DEF7FF;
        border-radius: 12px;
        padding: 16px;
        min-height: 150px;
    }

    .st-key-my-free-space {
        background-color: #DEF7FF;
        border-radius: 12px;
        padding: 16px;
        min-height: 150px;
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


st.markdown("<h1 style='color: #191970;'>Registro de movimientos</h1>", unsafe_allow_html=True)

try:
	movements = load_movements()
except (OSError, ValueError) as error:
	st.error(f"No se pudo cargar el registro de movimientos: {error}")
else:
	if movements:
		confirm_clear = st.checkbox(
			"Confirmo que deseo borrar todo el historial de movimientos"
		)
		if st.button("Borrar historial", disabled=not confirm_clear):
			try:
				clear_movements()
			except OSError as error:
				st.error(f"No se pudo borrar el registro de movimientos: {error}")
			else:
				movements = []
				st.success("Se borró el historial. Las muestras de las cajas no se modificaron.")

	if not movements:
		st.info("Todavía no hay movimientos registrados.")
	else:
		movement_table = pd.DataFrame(movements).rename(columns={
			"timestamp": "Fecha y hora",
			"action": "Movimiento",
			"box": "Caja criogénica",
			"location": "Ubicación",
			"sample_id": "ID de muestra",
		})
		movement_table["_sort_timestamp"] = pd.to_datetime(
			movement_table["Fecha y hora"], errors="coerce", utc=True
		)
		movement_table = movement_table.sort_values(
			"_sort_timestamp", ascending=False
		).drop(columns="_sort_timestamp")
		st.dataframe(movement_table, hide_index=True, width="stretch")
		st.download_button(
			"Descargar registro CSV",
			data=movement_table.to_csv(index=False).encode("utf-8-sig"),
			file_name="registro_movimientos.csv",
			mime="text/csv",
		)
