#----------------------------------------------------------------------
#Página de navegación donde venga el mapa completo de muestras que se 
#encuentran en el congelador
#Por: Andrea Solis 593315
#----------------------------------------------------------------------

#Importar librerias----------------------------------------------------
import streamlit as st
import pandas as pd
from gspread import service_account_from_dict
from gspread.exceptions import GSpreadException
from google.auth.exceptions import GoogleAuthError
from requests.exceptions import RequestException
from streamlit_gsheets import GSheetsConnection

from movements import (
    MOVEMENT_COLUMNS,
    MOVEMENTS_WORKSHEET,
    clear_movement_sheet_cache,
    record_movement,
)

#Funciones------------------------------------------------------------------
SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "17AfEVk6-HmFNwNxpngwp-cttRaFaqpZFnmRBAzDRUXo/edit"
)
SHEET_COLUMNS = [
    "ubicacion",
    "id",
    "fecha",
    "responsable",
    "numero_pases",
    "criopreservante",
    "lugar_proveniencia",
    "certificacion",
    "numero_celulas",
]
def _sheet_text(value):
    if pd.isna(value):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _parse_certification(value):
    if isinstance(value, bool):
        return value
    text = _sheet_text(value).casefold()
    if text in {"true", "verdadero", "sí", "si", "1"}:
        return True
    if text in {"false", "falso", "no", "0"}:
        return False
    if not text:
        return None
    raise ValueError(f"Valor no válido para certificación: {value}")


def _parse_location(value):
    parts = [part.strip() for part in _sheet_text(value).split(",")]
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Ubicación no válida en Google Sheets: {value}")
    number = str(int(parts[1])) if parts[1].isdigit() else parts[1]
    return parts[0].upper(), number


@st.cache_data(ttl=30)
def _read_sheet_data(worksheet):
    connection = st.connection("gsheets", type=GSheetsConnection)
    return connection.read(
        spreadsheet=SPREADSHEET_URL,
        worksheet=worksheet,
        ttl=0,
    )


def read_sheet(box):
    data = _read_sheet_data(box["worksheet"])
    missing_columns = set(SHEET_COLUMNS).difference(data.columns)
    if missing_columns:
        raise ValueError(
            f"La pestaña {box['worksheet']} no tiene las columnas requeridas: "
            f"{', '.join(sorted(missing_columns))}"
        )

    data = data.dropna(how="all").copy()
    valid_rows = []
    for index, row in data.iterrows():
        location = _sheet_text(row["ubicacion"])
        if not location:
            if any(_sheet_text(value) for value in row):
                raise ValueError(
                    f"Hay datos sin ubicación en la pestaña {box['worksheet']}."
                )
            continue
        valid_rows.append(index)
    return data.loc[valid_rows].reset_index(drop=True)


def samples_from_sheet(data):
    samples = {}
    for _, row in data.iterrows():
        location = _parse_location(row["ubicacion"])
        if location in samples:
            raise ValueError(f"Ubicación duplicada en Google Sheets: {location}")
        samples[location] = {
            "id": _sheet_text(row["id"]),
            "fecha": _sheet_text(row["fecha"]),
            "responsable": _sheet_text(row["responsable"]),
            "numero_pases": _sheet_text(row["numero_pases"]),
            "criopreservante": _sheet_text(row["criopreservante"]),
            "lugar_proveniencia": _sheet_text(row["lugar_proveniencia"]),
            "certificacion": _parse_certification(row["certificacion"]),
            "numero_celulas": _sheet_text(row["numero_celulas"]),
        }
    return samples


def append_sample_row(data, location, sample):
    row = {column: "" for column in data.columns}
    row.update(
        {
            "ubicacion": f"{location[0]},{location[1]}",
            "id": sample["id"],
            "fecha": sample["fecha"],
            "responsable": sample["responsable"],
            "numero_pases": sample["numero_pases"],
            "criopreservante": sample["criopreservante"],
            "lugar_proveniencia": sample["lugar_proveniencia"],
            "certificacion": sample["certificacion"],
            "numero_celulas": sample["numero_celulas"],
        }
    )
    return pd.concat([data, pd.DataFrame([row])], ignore_index=True)


def update_sheet(connection, box, data):
    connection.update(
        spreadsheet=SPREADSHEET_URL,
        worksheet=box["worksheet"],
        data=data,
    )


@st.cache_resource
def _movement_worksheet():
    credentials = st.secrets["connections"]["gsheets"].to_dict()
    client = service_account_from_dict(credentials)
    spreadsheet = client.open_by_url(SPREADSHEET_URL)
    worksheet = spreadsheet.worksheet(MOVEMENTS_WORKSHEET)
    headers = worksheet.row_values(1)
    if headers != MOVEMENT_COLUMNS:
        raise ValueError(
            f"La pestaña '{MOVEMENTS_WORKSHEET}' debe tener estos encabezados "
            f"en la fila 1, en este orden: {', '.join(MOVEMENT_COLUMNS)}"
        )
    return worksheet


def record_movement_in_sheets(action, box_name, location, sample):
    try:
        movement = record_movement(action, box_name, location, sample)
    except OSError as exc:
        st.session_state["sample_notice"] = (
            f"La muestra se actualizó en Google Sheets, pero no se pudo guardar "
            f"el movimiento en el registro local: {exc}"
        )
        st.session_state["sample_notice_type"] = "error"
        return False

    try:
        _movement_worksheet().append_row(
            [movement[column] for column in MOVEMENT_COLUMNS],
            value_input_option="RAW",
        )
        clear_movement_sheet_cache()
    except RequestException as exc:
        st.session_state["sample_notice"] = (
            f"La muestra se actualizó y el movimiento quedó en el registro local, "
            f"pero se interrumpió la conexión al guardar el movimiento en Google Sheets: "
            f"{exc} Revise la pestaña '{MOVEMENTS_WORKSHEET}' antes de volver a añadir "
            "el movimiento manualmente, por si Google alcanzó a guardarlo."
        )
        st.session_state["sample_notice_type"] = "error"
        return False
    except (AttributeError, KeyError, ValueError, OSError) as exc:
        st.session_state["sample_notice"] = (
            f"La muestra se actualizó y el movimiento quedó en el registro local, "
            f"pero no se pudo configurar la pestaña de historial de Google Sheets: {exc}"
        )
        st.session_state["sample_notice_type"] = "error"
        return False
    except (GSpreadException, GoogleAuthError, TimeoutError, ConnectionError) as exc:
        st.session_state["sample_notice"] = (
            f"La muestra se actualizó y el movimiento quedó en el registro local, "
            f"pero no se pudo añadir a la pestaña de Google Sheets '{MOVEMENTS_WORKSHEET}'. "
            f"Verifique que la pestaña exista y tenga los encabezados indicados "
            f"en GOOGLE_SHEETS_SETUP.md. Error: {exc}"
        )
        st.session_state["sample_notice_type"] = "error"
        return False

    return True


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
BOXES = [
    {
        "key": "humana_cancerosa",
        "name": "Caja criogénica humana cancerosa",
        "worksheet": "samples_humana_cancerosa",
    },
    {
        "key": "humana_no_cancerosa",
        "name": "Caja criogénica humana no cancerosa",
        "worksheet": "samples_humana_no_cancerosa",
    },
    {
        "key": "raton_cancerosa",
        "name": "Caja criogénica ratón cancerosa",
        "worksheet": "samples_raton_cancerosa",
    },
    {
        "key": "raton_no_cancerosa",
        "name": "Caja criogénica ratón no cancerosa",
        "worksheet": "samples_raton_no_cancerosa",
    },
]
BOXES_BY_KEY = {box["key"]: box for box in BOXES}

connection = st.connection("gsheets", type=GSheetsConnection)
try:
    samples_by_box = {
        box["key"]: samples_from_sheet(read_sheet(box))
        for box in BOXES
    }
except Exception as exc:
    st.error(
        "No se pudieron leer las muestras de Google Sheets. Esta app requiere "
        "una cuenta de servicio configurada y compartida con la hoja. Si aparece "
        "HTTP 429, Google limitó temporalmente las lecturas; espere un minuto y "
        "vuelva a intentar. Consulte GOOGLE_SHEETS_SETUP.md para más información."
    )
    st.exception(exc)
    st.stop()


def remove_sample(box_key):
    box = BOXES_BY_KEY[box_key]
    letter_key = f"{box_key}_letter_ext"
    number_key = f"{box_key}_number_ext"
    letter = str(st.session_state.get(letter_key, "")).strip().upper()
    number = str(st.session_state.get(number_key, "")).strip()
    if number.isdigit():
        number = str(int(number))
    toremove = (letter, number)

    try:
        sheet_data = read_sheet(box)
        current = samples_from_sheet(sheet_data)
    except Exception as e:
        st.session_state["sample_notice"] = f"Error al leer Google Sheets: {e}"
        st.session_state["sample_notice_type"] = "error"
        return

    if toremove not in current:
        st.session_state["sample_notice"] = f"No existe muestra en la posición {toremove} de {box['name']}"
        st.session_state["sample_notice_type"] = "warning"
        return

    try:
        remaining_rows = sheet_data[
            sheet_data["ubicacion"].map(
                lambda value: _parse_location(value) != toremove
            )
        ].reset_index(drop=True)
        update_sheet(connection, box, remaining_rows)
        _read_sheet_data.clear(box["worksheet"])
    except Exception as e:
        st.session_state["sample_notice"] = f"Error al guardar cambios en Google Sheets: {e}"
        st.session_state["sample_notice_type"] = "error"
        return

    st.session_state[letter_key] = ""
    st.session_state[number_key] = ""
    if not record_movement_in_sheets("Salida", box["name"], toremove, current[toremove]):
        return
    st.session_state["sample_notice"] = (
        f"Se removió la muestra en {toremove} de {box['name']} y se guardó el "
        "movimiento en Google Sheets"
    )
    st.session_state["sample_notice_type"] = "success"


def add_sample(box_key):
    box = BOXES_BY_KEY[box_key]
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
    if number.isdigit():
        number = str(int(number))
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
    try:
        sheet_data = read_sheet(box)
        current = samples_from_sheet(sheet_data)
    except Exception as e:
        st.session_state["sample_notice"] = f"Error al leer Google Sheets: {e}"
        st.session_state["sample_notice_type"] = "error"
        return

    if toadd in current:
        st.session_state["sample_notice"] = f"Ya existe una muestra en la posición {toadd} de {box['name']} (ID: {current[toadd].get('id')})."
        st.session_state["sample_notice_type"] = "warning"
        return

    new_sample = {
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
        updated_rows = append_sample_row(sheet_data, toadd, new_sample)
        update_sheet(connection, box, updated_rows)
        _read_sheet_data.clear(box["worksheet"])
    except Exception as e:
        st.session_state["sample_notice"] = f"Error al guardar cambios en Google Sheets: {e}"
        st.session_state["sample_notice_type"] = "error"
        return

    if not record_movement_in_sheets("Entrada", box["name"], toadd, new_sample):
        return
    for widget_key in (
        letter_key, number_key, id_key, date_key, responsible_key,
        cryoprotectant_key, provenance_key,
    ):
        st.session_state[widget_key] = ""
    st.session_state[passages_key] = ""
    st.session_state[certification_key] = False
    st.session_state[cell_count_key] = ""
    st.session_state["sample_notice"] = (
        f"Se añadió la muestra en {toadd} (ID: {sample_id}) a {box['name']} "
        "y se guardó el movimiento en Google Sheets"
    )
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
    samples = samples_by_box[box_key]

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
            with st.form(key=f"remove_form_{box_key}"):
                st.write("Escriba la ubicación de la muestra que desea extraer")
                st.text_input("Letra (Ej. A)", max_chars=1, key=f"{box_key}_letter_ext")
                st.text_input("Número (Ej. 1)", max_chars=2, key=f"{box_key}_number_ext")
                st.form_submit_button(
                    "Extraer muestra",
                    use_container_width=True,
                    key=f"remove_{box_key}",
                    on_click=remove_sample,
                    args=(box_key,),
                )

        with addsamp:
            st.markdown('<p class="sample-form-subtitle">Añadir Muestra</p>', unsafe_allow_html=True)
            with st.form(key=f"add_form_{box_key}"):
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
                st.form_submit_button(
                    "Añadir muestra",
                    use_container_width=True,
                    key=f"add_{box_key}",
                    on_click=add_sample,
                    args=(box_key,),
                )
