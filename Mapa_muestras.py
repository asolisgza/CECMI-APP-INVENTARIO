#----------------------------------------------------------------------
#Página de navegación donde venga el mapa completo de muestras que se 
#encuentran en el congelador
#Por: Andrea Solis 593315
#----------------------------------------------------------------------

#Importar librerias----------------------------------------------------
import streamlit as st
import pandas as pd
#Para crear databases
import os
import json
import tempfile 

#Funciones------------------------------------------------------------------
#Funcion para inicializar datos
DATA_FILE = os.path.join(os.path.dirname(__file__), "samples.json")

# Funcion para convertir ("A", "1") a "A,1"
def _serialize_samples(samples):
    return {f"{k[0]},{k[1]}": v for k, v in samples.items()}

# Funcion para convertir "A,1" a ("A", "1")
def _deserialize_samples(obj):
    # Be tolerant of spaces in keys (e.g., "A, 1") by stripping parts
    result = {}
    for k, v in obj.items():
        parts = [p.strip() for p in k.split(",")]
        result[tuple(parts)] = v
    return result


def save_samples(samples, path=DATA_FILE):
    # Write atomically to avoid corrupting the file
    tmp_fd, tmp_path = tempfile.mkstemp(prefix="samples_", suffix=".json", dir=os.path.dirname(path) or ".")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(_serialize_samples(samples), f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise


def load_samples(path=DATA_FILE, default=None):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _deserialize_samples(data)
    return default if default is not None else {}

#Funcion para asignar el color de fondo de tabla
def assign_color_to_map(val):
    if pd.isna(val) or val is None:
        return "background-color: #FFFFFF; color: #0A3463"  # Espacio blanco
    else:
        return"background-color: #023328; color:#FFFFFF" #Espacio verde y texto blanco


#Procesos previos------------------------------------------------------------
if 'clicked' not in st.session_state:
    st.session_state.clicked = False


def click_button():
    st.session_state.clicked =True


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
    .st-key-my-cont1 {
        background-color: #DEF7FF;
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

#Datos ----------------------------------------------------
#TABLA DE DATOS
#Tabla de contenedor 1--------------------------------------------------------

_default_samples = {
    ("A", "1"): {"id": "M-101", "fecha": "2026-01-15"},
    ("A", "3"): {"id": "M-102", "fecha": "2026-02-10"},
    ("B", "2"): {"id": "M-103", "fecha": "2026-03-01"},
    ("C", "5"): {"id": "M-104", "fecha": "2026-03-20"},
}

# Initialize session state from file or default
if "sample" not in st.session_state:
    samples = load_samples(DATA_FILE, default=_default_samples)
    st.session_state["sample"] = samples
    # If no file existed yet, create it so future runs persist
    if not os.path.exists(DATA_FILE):
        save_samples(samples, DATA_FILE)

rows = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
columns = [str(i) for i in range(1, 11)]

mat1 = {}
for col in columns:
    mat1[col] = [
        st.session_state.sample.get((f, col), {}).get("id", None)
        for f in rows
    ]
#Número de muestras en caja
num_samples_cont1 = len(st.session_state.sample)

#Número total de espacio
num_total_space = 50

#Porcentaje
por_free_space = ((num_total_space - num_samples_cont1)*100)/num_total_space

#Contenido de la página---------------------------------------------------

#Encabezado
st.markdown("<h1 style='color: #191970;'>Mapa de Muestras</h1>", unsafe_allow_html=True)
st.write("Mapas de cajas criogénicas")


#Contenedor 1
with st.container(key="my-cont1"):
    st.subheader("Caja criogénica 1")
    container1 = pd.DataFrame(mat1, index=rows)
    styled_cont1 = container1.style.map(assign_color_to_map)

    #Hacer interactiva
    event = st.dataframe(
        styled_cont1,
        on_select="rerun",
        selection_mode="single-cell",
        width = "stretch"
    )

    row_let = "A"
    col_num = "1"

    if event.selection and event.selection["cells"]:
        cell1 = event.selection["cells"][0]
        row_num = cell1[0]
        col_num = cell1[1]
        
        row_let = rows[row_num]
        posicion = f"{row_let}{col_num}"
        
    # Obtener los datos si existe la muestra
    if (row_let, col_num) in st.session_state.sample:
        datos_muestra = st.session_state.sample.get((row_let, col_num))
    else:
        datos_muestra = {"id":"None", "fecha":"N/A"}

    st.write("Haz clic en cualquier celda para consultar su fecha de registro:")
    wrposition = row_let + "," + col_num
    col1, col2, col3 = st.columns(3)
    col1.metric("Posición", wrposition)
    col2.metric("ID de Muestra", datos_muestra["id"])
    col3.metric("Fecha de Registro", datos_muestra["fecha"])


extsamp, addsamp = st.columns(2)

with extsamp:
    st.subheader("Extraer Muestra")
    st.write("Escriba la ubicación de la muestra que desea extraer")
    letter_ext = st.text_input("Letra (Ej. A)", max_chars=1, key="letter_ext")
    number_ext = st.text_input("Número (Ej. 1)", max_chars=2, key="number_ext")
    if st.button("Extraer muestra", use_container_width=True):
        toremove = (str(letter_ext).upper(), str(number_ext))
        if toremove in st.session_state.get("sample", {}):
            # Remove and persist
            new_sample = {k: v for k, v in st.session_state["sample"].items() if k != toremove}
            st.session_state["sample"] = new_sample
            try:
                save_samples(new_sample, DATA_FILE)
            except Exception as e:
                st.error(f"Error al guardar cambios: {e}")
            else:
                st.success(f"Se removió la muestra en {toremove} y se guardó en disco")
        else:
            st.warning(f"No existe muestra en la posición {toremove}")
            
with addsamp:
    st.subheader("Añadir Muestra")
    st.write("Escriba la siguiente información de la muestra que desea añadir")
    letter_add = st.text_input("Ubicación: Letra (Ej. A)", max_chars=1, key="letter_add")
    number_add = st.text_input("Ubicación: Número (Ej. 1)", max_chars=2, key="number_add")
    id_add = st.text_input("ID (Ej. M-100)", key="id_add")
    fecha_add = st.text_input("Fecha de Registro (AAAA-MM-DD)", key="fecha_add")

    if st.button("Añadir muestra", use_container_width=True):
        # Normalize inputs
        letter = str(letter_add).strip().upper()
        number = str(number_add).strip()

        if not letter or not number or not id_add:
            st.warning("Por favor complete letra, número e ID de la muestra antes de añadir.")
        else:
            toadd = (letter, number)
            current = st.session_state.get("sample", {})
            if toadd in current:
                st.warning(f"Ya existe una muestra en la posición {toadd} (ID: {current[toadd].get('id')}).")
            else:
                # Create a new dict with the added sample and reassign so Streamlit detects change
                new_sample = {k: v for k, v in current.items()}
                new_sample[toadd] = {"id": id_add, "fecha": fecha_add}
                st.session_state["sample"] = new_sample
                try:
                    save_samples(new_sample, DATA_FILE)
                except Exception as e:
                    st.error(f"Error al guardar cambios: {e}")
                else:
                    st.success(f"Se añadió la muestra en {toadd} (ID: {id_add}) y se guardó en disco")


