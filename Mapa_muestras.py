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
    [class*="st-key-box_"] {
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

    .sample-form-subtitle {
        color: #0284c7;
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
    }

    /* Keep sample-entry fields white */
    .stTextInput [data-baseweb="input"],
    .stTextInput input {
        background-color: #FFFFFF !important;
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

BOXES = [
    {
        "key": "humana_cancerosa",
        "name": "Caja criogénica humana cancerosa",
        "path": DATA_FILE,
        "default": _default_samples,
    },
    {
        "key": "humana_no_cancerosa",
        "name": "Caja criogénica humana no cancerosa",
        "path": os.path.join(os.path.dirname(__file__), "samples_humana_no_cancerosa.json"),
        "default": {},
    },
    {
        "key": "raton_cancerosa",
        "name": "Caja criogénica ratón cancerosa",
        "path": os.path.join(os.path.dirname(__file__), "samples_raton_cancerosa.json"),
        "default": {},
    },
    {
        "key": "raton_no_cancerosa",
        "name": "Caja criogénica ratón no cancerosa",
        "path": os.path.join(os.path.dirname(__file__), "samples_raton_no_cancerosa.json"),
        "default": {},
    },
]
BOXES_BY_KEY = {box["key"]: box for box in BOXES}

# Each box uses its own session-state entry and JSON file. The existing samples.json
# remains assigned to the original box so its data is preserved.
for box in BOXES:
    state_key = f"samples_{box['key']}"
    if state_key not in st.session_state:
        if box["key"] == "humana_cancerosa" and "sample" in st.session_state:
            samples = st.session_state["sample"]
        else:
            samples = load_samples(box["path"], default=box["default"])
        st.session_state[state_key] = samples
        if box["key"] == "humana_cancerosa" and not os.path.exists(box["path"]):
            save_samples(samples, box["path"])


def remove_sample(box_key):
    box = BOXES_BY_KEY[box_key]
    state_key = f"samples_{box_key}"
    letter_key = f"{box_key}_letter_ext"
    number_key = f"{box_key}_number_ext"
    letter = str(st.session_state.get(letter_key, "")).strip().upper()
    number = str(st.session_state.get(number_key, "")).strip()
    toremove = (letter, number)
    current = st.session_state[state_key]

    if toremove not in current:
        st.session_state["sample_notice"] = f"No existe muestra en la posición {toremove} de {box['name']}"
        st.session_state["sample_notice_type"] = "warning"
        return

    new_sample = {k: v for k, v in current.items() if k != toremove}
    try:
        save_samples(new_sample, box["path"])
    except Exception as e:
        st.session_state["sample_notice"] = f"Error al guardar cambios: {e}"
        st.session_state["sample_notice_type"] = "error"
        return

    st.session_state[state_key] = new_sample
    st.session_state[letter_key] = ""
    st.session_state[number_key] = ""
    st.session_state["sample_notice"] = f"Se removió la muestra en {toremove} de {box['name']} y se guardó en disco"
    st.session_state["sample_notice_type"] = "success"


def add_sample(box_key):
    box = BOXES_BY_KEY[box_key]
    state_key = f"samples_{box_key}"
    letter_key = f"{box_key}_letter_add"
    number_key = f"{box_key}_number_add"
    id_key = f"{box_key}_id_add"
    date_key = f"{box_key}_fecha_add"
    responsible_key = f"{box_key}_responsable_add"
    passages_key = f"{box_key}_pases_add"
    cryoprotectant_key = f"{box_key}_criopreservante_add"
    provenance_key = f"{box_key}_proveniencia_add"
    certification_key = f"{box_key}_certificacion_add"
    cell_count_key = f"{box_key}_celulas_add"
    letter = str(st.session_state.get(letter_key, "")).strip().upper()
    number = str(st.session_state.get(number_key, "")).strip()
    sample_id = str(st.session_state.get(id_key, "")).strip()
    fecha = str(st.session_state.get(date_key, "")).strip()
    responsable = str(st.session_state.get(responsible_key, "")).strip()
    numero_pases = str(st.session_state.get(passages_key, "")).strip()
    criopreservante = str(st.session_state.get(cryoprotectant_key, "")).strip()
    lugar_proveniencia = str(st.session_state.get(provenance_key, "")).strip()
    certificacion = st.session_state.get(certification_key, False)
    numero_celulas = str(st.session_state.get(cell_count_key, "")).strip()

    if not letter or not number or not sample_id:
        st.session_state["sample_notice"] = "Por favor complete letra, número e ID de la muestra antes de añadir."
        st.session_state["sample_notice_type"] = "warning"
        return

    toadd = (letter, number)
    current = st.session_state[state_key]
    if toadd in current:
        st.session_state["sample_notice"] = f"Ya existe una muestra en la posición {toadd} de {box['name']} (ID: {current[toadd].get('id')})."
        st.session_state["sample_notice_type"] = "warning"
        return

    new_sample = {k: v for k, v in current.items()}
    new_sample[toadd] = {
        "id": sample_id,
        "fecha": fecha,
        "responsable": responsable,
        "numero_pases": numero_pases,
        "criopreservante": criopreservante,
        "lugar_proveniencia": lugar_proveniencia,
        "certificacion": certificacion,
        "numero_celulas": numero_celulas,
    }
    try:
        save_samples(new_sample, box["path"])
    except Exception as e:
        st.session_state["sample_notice"] = f"Error al guardar cambios: {e}"
        st.session_state["sample_notice_type"] = "error"
        return

    st.session_state[state_key] = new_sample
    for widget_key in (
        letter_key, number_key, id_key, date_key, responsible_key,
        cryoprotectant_key, provenance_key,
    ):
        st.session_state[widget_key] = ""
    st.session_state[passages_key] = ""
    st.session_state[certification_key] = False
    st.session_state[cell_count_key] = ""
    st.session_state["sample_notice"] = f"Se añadió la muestra en {toadd} (ID: {sample_id}) a {box['name']} y se guardó en disco"
    st.session_state["sample_notice_type"] = "success"

#Contenido de la página---------------------------------------------------

#Encabezado
st.markdown("<h1 style='color: #191970;'>Mapa de Muestras</h1>", unsafe_allow_html=True)
st.write("Mapas de cajas criogénicas")
st.markdown("**Ir directamente a una caja:**")
for box in BOXES:
    st.markdown(f"- [{box['name']}](#box-{box['key']})")

if "sample_notice" in st.session_state:
    notice = st.session_state.pop("sample_notice")
    notice_type = st.session_state.pop("sample_notice_type", "success")
    getattr(st, notice_type)(notice)


#Display all four independent boxes
rows = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
columns = [str(i) for i in range(1, 11)]

for box in BOXES:
    box_key = box["key"]
    state_key = f"samples_{box_key}"
    samples = st.session_state[state_key]

    st.markdown(f'<span id="box-{box_key}"></span>', unsafe_allow_html=True)
    with st.container(key=f"box_{box_key}"):
        st.subheader(box["name"])

        matrix = {
            col: [samples.get((row, col), {}).get("id", None) for row in rows]
            for col in columns
        }
        box_table = pd.DataFrame(matrix, index=rows)
        styled_table = box_table.style.map(assign_color_to_map)
        event = st.dataframe(
            styled_table,
            on_select="rerun",
            selection_mode="single-cell",
            width="stretch",
            key=f"map_{box_key}",
        )

        row_let = "A"
        col_num = "1"
        if event.selection and event.selection["cells"]:
            cell = event.selection["cells"][0]
            row_let = rows[cell[0]]
            col_num = cell[1]

        datos_muestra = samples.get(
            (row_let, col_num), {"id": "None", "fecha": "N/A"}
        )
        st.write("Haz clic en cualquier celda para consultar su fecha de registro:")
        col1, col2, col3 = st.columns(3)
        col1.metric("Posición", f"{row_let},{col_num}")
        col2.metric("Nombre de línea celular", datos_muestra.get("id", "No registrado"))
        col3.metric("Fecha de Congelación", datos_muestra.get("fecha", "No registrada"))

        detalle_cols = st.columns(3)
        detalle_cols[0].metric("Responsable", datos_muestra.get("responsable", "No registrado"))
        detalle_cols[1].metric("Número de Pases", datos_muestra.get("numero_pases", "No registrado"))
        detalle_cols[2].metric("Criopreservante", datos_muestra.get("criopreservante", "No registrado"))
        detalle_cols = st.columns(3)
        detalle_cols[0].metric("Lugar de proveniencia", datos_muestra.get("lugar_proveniencia", "No registrado"))
        certificacion = datos_muestra.get("certificacion")
        certificacion_texto = "Sí" if certificacion is True else "No" if certificacion is False else "No registrado"
        detalle_cols[1].metric("Con certificación", certificacion_texto)
        detalle_cols[2].metric("Número de células en el vial", datos_muestra.get("numero_celulas", "No registrado"))

        extsamp, addsamp = st.columns(2)
        with extsamp:
            st.markdown('<p class="sample-form-subtitle">Extraer Muestra</p>', unsafe_allow_html=True)
            st.write("Escriba la ubicación de la muestra que desea extraer")
            st.text_input("Letra (Ej. A)", max_chars=1, key=f"{box_key}_letter_ext")
            st.text_input("Número (Ej. 1)", max_chars=2, key=f"{box_key}_number_ext")
            st.button(
                "Extraer muestra",
                use_container_width=True,
                key=f"remove_{box_key}",
                on_click=remove_sample,
                args=(box_key,),
            )

        with addsamp:
            st.markdown('<p class="sample-form-subtitle">Añadir Muestra</p>', unsafe_allow_html=True)
            st.write("Escriba la siguiente información de la muestra que desea añadir")
            add_col1, add_col2 = st.columns(2)
            add_col1.text_input("Ubicación: Letra (Ej. A)", max_chars=1, key=f"{box_key}_letter_add")
            add_col2.text_input("Ubicación: Número (Ej. 1)", max_chars=2, key=f"{box_key}_number_add")

            add_col1, add_col2 = st.columns(2)
            add_col1.text_input("Nombre de línea celular (Ej. HeLa)", key=f"{box_key}_id_add")
            add_col2.text_input("Fecha de Congelación (AAAA-MM-DD)", key=f"{box_key}_fecha_add")

            add_col1, add_col2 = st.columns(2)
            add_col1.text_input("Responsable", key=f"{box_key}_responsable_add")
            add_col2.text_input("Número de Pases", key=f"{box_key}_pases_add")

            add_col1, add_col2 = st.columns(2)
            add_col1.text_input("Criopreservante", key=f"{box_key}_criopreservante_add")
            add_col2.text_input("Lugar de proveniencia", key=f"{box_key}_proveniencia_add")

            add_col1, add_col2 = st.columns(2)
            add_col1.checkbox("Con certificación", key=f"{box_key}_certificacion_add")
            add_col2.text_input("Número de células en el vial", key=f"{box_key}_celulas_add")
            st.button(
                "Añadir muestra",
                use_container_width=True,
                key=f"add_{box_key}",
                on_click=add_sample,
                args=(box_key,),
            )


