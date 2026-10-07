#-----------------------------------------------------------------------
#Página Web de CECMI para el registro digital de elementos en congelador de -80°C
#Autora: Andrea Solis, 593315
#------------------------------------------------------------------------

#Importar librerias--------------------------------------------------------
import streamlit as st
import pandas as pd
import json
import os

APP_DIR = os.path.dirname(__file__)
SAMPLE_BOXES = [
    {
        "name": "Caja criogénica humana cancerosa",
        "path": os.path.join(APP_DIR, "samples.json"),
        "default": {
            "A,1": {"id": "M-101", "fecha": "2026-01-15"},
            "A,3": {"id": "M-102", "fecha": "2026-02-10"},
            "B,2": {"id": "M-103", "fecha": "2026-03-01"},
            "C,5": {"id": "M-104", "fecha": "2026-03-20"},
        },
    },
    {
        "name": "Caja criogénica humana no cancerosa",
        "path": os.path.join(APP_DIR, "samples_humana_no_cancerosa.json"),
        "default": {},
    },
    {
        "name": "Caja criogénica ratón cancerosa",
        "path": os.path.join(APP_DIR, "samples_raton_cancerosa.json"),
        "default": {},
    },
    {
        "name": "Caja criogénica ratón no cancerosa",
        "path": os.path.join(APP_DIR, "samples_raton_no_cancerosa.json"),
        "default": {},
    },
]


def load_samples(path, default=None):
    """Load sample data from JSON, converting serialized locations to tuples."""
    if not os.path.exists(path):
        return default or {}

    with open(path, "r", encoding="utf-8") as sample_file:
        stored_samples = json.load(sample_file)
    return {
        tuple(part.strip() for part in location.split(",")): sample
        for location, sample in stored_samples.items()
    }

# Read each box's persisted data so this dashboard reflects updates made on the map page.
total_samples = sum(
    len(load_samples(box["path"], default=box["default"]))
    for box in SAMPLE_BOXES
)
total_capacity = len(SAMPLE_BOXES) * 10 * 10
free_space_percentage = (total_capacity - total_samples) / total_capacity * 100


def load_all_sample_rows():
    """Combine samples from every box into rows for the inventory search."""
    sample_rows = []
    for box in SAMPLE_BOXES:
        samples = load_samples(box["path"], default=box["default"])
        for (letter, number), sample in samples.items():
            certification = sample.get("certificacion")
            if certification is None:
                certification_label = "No registrado"
            elif isinstance(certification, str):
                certification_label = "Sí" if certification.strip().casefold() in {"sí", "si", "true", "1"} else "No"
            else:
                certification_label = "Sí" if certification else "No"

            sample_rows.append({
                "Nombre de línea": sample.get("id", ""),
                "Caja criogénica": box["name"],
                "Ubicación": f"{letter},{number}",
                "Responsable": sample.get("responsable", ""),
                "Fecha de congelación": sample.get("fecha", ""),
                "Con certificado": certification_label,
                "Número de pases": sample.get("numero_pases", ""),
                "Criopreservante": sample.get("criopreservante", ""),
                "Lugar de proveniencia": sample.get("lugar_proveniencia", ""),
                "Número de células en el vial": sample.get("numero_celulas", ""),
            })
    return pd.DataFrame(
        sample_rows,
        columns=[
            "Nombre de línea",
            "Caja criogénica",
            "Ubicación",
            "Responsable",
            "Fecha de congelación",
            "Con certificado",
            "Número de pases",
            "Criopreservante",
            "Lugar de proveniencia",
            "Número de células en el vial",
        ],
    )

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

#Contenido de la página ------------------------------------------------

#Encabezado
st.markdown("<h1 style='color: #191970;'>Inventario Digital de Congelador CECMI</h1>", unsafe_allow_html=True)
st.write("Gestión de muestras y ubicación")

#Resumen
st.header("Datos principales")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(key="my-temperature", height=160):
        icon_col, text_col = st.columns([1, 2])

        with icon_col:
            st.image("thermometer.svg", width=75)

        with text_col:
            st.metric("Temperatura", "-80 °C")

with col2:
    with st.container(key="my-samples", height=160):
        icon_col, text_col = st.columns([1, 2])
        
        with icon_col:
            st.image("real_sample.svg", width=115)
        
        with text_col:
            st.metric("Muestras almacenadas", total_samples)

with col3:
    with st.container(key="my-free-space", height=160):
        icon_col, text_col = st.columns([1, 2])
                
        with icon_col:
            st.image("sample.svg", width=115)
        
        with text_col:
            st.metric("Espacio libre", f"{free_space_percentage:.1f}%")

#Buscador de muestras
st.header("Buscador de muestras")
st.write("Filtra las muestras por sus características. La ubicación se muestra en los resultados, pero no se usa como filtro.")

with st.form("sample_search_form"):
    filter_row1 = st.columns(3)
    name_filter = filter_row1[0].text_input("Nombre de línea celular", key="search_name")
    box_options = ["Todas las cajas"] + [box["name"] for box in SAMPLE_BOXES]
    box_filter = filter_row1[1].selectbox("Caja criogénica", box_options, key="search_box")
    responsible_filter = filter_row1[2].text_input("Responsable", key="search_responsible")

    filter_row2 = st.columns(3)
    date_filter = filter_row2[0].text_input("Fecha de congelación (AAAA-MM-DD)", key="search_date")
    certification_filter = filter_row2[1].selectbox(
        "Con certificado",
        ["Todos", "Sí", "No", "No registrado"],
        key="search_certification",
    )
    passages_filter = filter_row2[2].text_input("Número de pases", key="search_passages")

    filter_row3 = st.columns(3)
    cryoprotectant_filter = filter_row3[0].text_input("Criopreservante", key="search_cryoprotectant")
    provenance_filter = filter_row3[1].text_input("Lugar de proveniencia", key="search_provenance")
    cell_count_filter = filter_row3[2].text_input("Número de células en el vial", key="search_cell_count")
    st.form_submit_button("Buscar muestras", use_container_width=True)

inventory = load_all_sample_rows()
filtered_inventory = inventory.copy()

text_filters = {
    "Nombre de línea": name_filter,
    "Responsable": responsible_filter,
    "Fecha de congelación": date_filter,
    "Número de pases": passages_filter,
    "Criopreservante": cryoprotectant_filter,
    "Lugar de proveniencia": provenance_filter,
    "Número de células en el vial": cell_count_filter,
}
for column_name, query in text_filters.items():
    if query.strip():
        filtered_inventory = filtered_inventory[
            filtered_inventory[column_name].astype(str).str.contains(
                query.strip(), case=False, na=False, regex=False
            )
        ]

if box_filter != "Todas las cajas":
    filtered_inventory = filtered_inventory[
        filtered_inventory["Caja criogénica"] == box_filter
    ]
if certification_filter != "Todos":
    filtered_inventory = filtered_inventory[
        filtered_inventory["Con certificado"] == certification_filter
    ]

st.caption(f"Muestras encontradas: {len(filtered_inventory)} de {len(inventory)}")
st.dataframe(filtered_inventory, hide_index=True, width="stretch")

#Listar recomendaciones de seguridad
st.subheader("Recomendaciones de seguridad")
st.markdown(
    """
    - Mantener la puerta abierta por menos de 45 segundos.
    - Registrar trazabilidad de principio a fin de cada vial.
    - Evitar que distintos tipos de células o niveles de riesgo biológicos se mezclen.
    - Las células más sensibles deben colocarse en las zonas centrales o inferiores.
    - Tener indicadores visibles en cada caja criogénica.
    - Mantener entre 10% y 15% de capacidad de almacenamiento libre.
    """
)


