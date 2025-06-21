import streamlit as st
import sqlite3
import datetime
from pathlib import Path
import pandas as pd
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env si existe
load_dotenv()

# --- Configuración de la Aplicación ---
DB_PATH = Path(__file__).parent / "asistencia.db"
APP_TITLE = "Registro de Asistencia INDETEC"

def load_user_credentials_from_env():
    """Carga las credenciales de usuario desde las variables de entorno."""
    creds = {}
    prefix = "APP_USER_"
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Obtiene el nombre de usuario de la variable (ej. de APP_USER_profe -> profe)
            username = key[len(prefix):].lower()
            if username: # Asegurarse de que el nombre de usuario no esté vacío
                creds[username] = value
    return creds

# Cargar credenciales al iniciar la aplicación
USER_CREDENTIALS = load_user_credentials_from_env()

STUDENTS_SETUP = {
    'sofia_sarachaga': {'nombre': 'Sofia Sarachaga'},
    'lailen_flores': {'nombre': 'Lailen Flores'},
    'gabriel_rios': {'nombre': 'Gabriel Rios'},
    'tahirah_husagh': {'nombre': 'Tahirah Husagh'},
    'josue_soler': {'nombre': 'Josue Soler'},
    'nehuen_cerdan': {'nombre': 'Nehuen Cerdan'},
}

# --- Funciones de Base de Datos ---
def init_db():
    """Inicializa la base de datos y las tablas si no existen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estudiantes (
            student_id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asistencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            fecha TEXT NOT NULL, -- YYYY-MM-DD
            estado TEXT, -- Presente, Ausente, Tarde
            causa TEXT,
            justificada INTEGER, -- 0 para No, 1 para Sí
            UNIQUE(student_id, fecha),
            FOREIGN KEY (student_id) REFERENCES estudiantes (student_id)
        )
    """)
    for student_id, data in STUDENTS_SETUP.items():
        cursor.execute("""
            INSERT INTO estudiantes (student_id, nombre) VALUES (?, ?)
            ON CONFLICT(student_id) DO UPDATE SET nombre=excluded.nombre
        """, (student_id, data['nombre']))
    conn.commit()
    conn.close()

def get_students():
    """Obtiene todos los estudiantes de la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, nombre FROM estudiantes ORDER BY nombre")
    students = [{'id': row[0], 'nombre': row[1]} for row in cursor.fetchall()]
    conn.close()
    return students

def get_attendance(student_id, date_str):
    """Obtiene la asistencia de un estudiante para una fecha específica."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT estado, causa, justificada FROM asistencias
        WHERE student_id = ? AND fecha = ?
    """, (student_id, date_str))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'estado': row[0], 'causa': row[1], 'justificada': bool(row[2])}
    return {'estado': '', 'causa': '', 'justificada': False}

def update_attendance(student_id, date_str, estado, causa, justificada):
    """Actualiza o inserta un registro de asistencia."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    justificada_int = 1 if justificada else 0
    
    if estado != 'Ausente':
        causa = ''
        justificada_int = 0

    cursor.execute("""
        INSERT INTO asistencias (student_id, fecha, estado, causa, justificada)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(student_id, fecha) DO UPDATE SET
            estado=excluded.estado,
            causa=excluded.causa,
            justificada=excluded.justificada
    """, (student_id, date_str, estado, causa, justificada_int))
    conn.commit()
    conn.close()

def get_all_attendance_for_student(student_id):
    """Obtiene todos los registros de asistencia para un estudiante, ordenados por fecha descendente."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fecha, estado, causa, justificada FROM asistencias
        WHERE student_id = ? ORDER BY fecha DESC
    """, (student_id,))
    records = [{'fecha': row[0], 'estado': row[1], 'causa': row[2], 'justificada': bool(row[3])}
               for row in cursor.fetchall()]
    conn.close()
    return records

# --- Funciones de Utilidad de Fechas ---
def get_monday_of_week(date_obj):
    return date_obj - datetime.timedelta(days=date_obj.weekday())

def get_week_days(monday_date):
    tuesday = monday_date + datetime.timedelta(days=1)
    thursday = monday_date + datetime.timedelta(days=3)
    return tuesday, thursday

# --- Componentes de Streamlit ---
def render_attendance_cell(student_id, student_name, date_obj, key_prefix, read_only=False):
    date_str = date_obj.strftime("%Y-%m-%d")
    current_attendance = get_attendance(student_id, date_str)
    estado_actual = current_attendance.get('estado', '')

    with st.container():
        if read_only:
            # Modo de solo lectura: solo mostrar el estado
            if not estado_actual:
                st.caption("No registrado")
            elif estado_actual == 'Presente':
                st.markdown(":green[●] Presente")
            elif estado_actual == 'Tarde':
                st.markdown(":orange[●] Tarde")
            elif estado_actual == 'Ausente':
                st.markdown(f":red[●] Ausente")
                causa = current_attendance.get('causa', '')
                justificada = current_attendance.get('justificada', False)
                if causa:
                    st.caption(f"Causa: {causa}")
                st.caption(f"Justificada: {'Sí' if justificada else 'No'}")
        else:
            # Modo de edición: mostrar widgets de entrada
            estado_options = ["", "Presente", "Ausente", "Tarde"]
            if estado_actual not in estado_options: estado_actual = ""

            estado = st.selectbox("Estado", options=estado_options, index=estado_options.index(estado_actual),
                                  key=f"{key_prefix}_estado_{student_id}_{date_str}", label_visibility="collapsed")
            causa = current_attendance.get('causa', '')
            justificada = current_attendance.get('justificada', False)

            if estado == 'Ausente':
                causa = st.text_input("Causa", value=causa, key=f"{key_prefix}_causa_{student_id}_{date_str}", placeholder="Causa de inasistencia")
                justificada = st.checkbox("Justificada", value=justificada, key=f"{key_prefix}_justificada_{student_id}_{date_str}")
            
            if (estado != current_attendance.get('estado') or
                (estado == 'Ausente' and (causa != current_attendance.get('causa') or justificada != current_attendance.get('justificada')))):
                update_attendance(student_id, date_str, estado, causa, justificada)
                st.toast(f"Asistencia de {student_name} para {date_obj.strftime('%d/%m')} guardada.", icon="💾")
                st.rerun()

def show_total_student_detail_dialog(student):
    """Muestra el diálogo con el detalle total de asistencia."""
    all_records = get_all_attendance_for_student(student['id'])
    
    dialog_title = f"Detalle Total de Asistencia: {student['nombre']}"
    try:
        _ = st.dialog(dialog_title)
    except AttributeError:
        st.error("La función de diálogo no está disponible en esta versión de Streamlit.")
        return

    if not all_records:
        st.write("No hay registros de asistencia para este estudiante.")
    else:
        total_presentes = sum(1 for r in all_records if r['estado'] == 'Presente')
        total_ausentes = sum(1 for r in all_records if r['estado'] == 'Ausente')
        total_tardes = sum(1 for r in all_records if r['estado'] == 'Tarde')
        total_registros = len(all_records)

        st.markdown(f"**Resumen General:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric(label="Días Registrados", value=total_registros)
        with col2: st.metric(label="Presentes", value=total_presentes)
        with col3: st.metric(label="Ausentes", value=total_ausentes)
        with col4: st.metric(label="Tardes", value=total_tardes)
        
        st.markdown("---")
        st.markdown("**Historial de Asistencias (más recientes primero):**")
        
        df_records = pd.DataFrame(all_records)
        df_records['fecha'] = pd.to_datetime(df_records['fecha']).dt.strftime('%d/%m/%Y')
        df_records['justificada'] = df_records['justificada'].apply(lambda x: 'Sí' if x else 'No')
        df_records = df_records.rename(columns={'fecha': 'Fecha', 'estado': 'Estado', 'causa': 'Causa', 'justificada': 'Justificada'})
        
        if total_ausentes == 0: df_to_show = df_records[['Fecha', 'Estado']]
        else: df_to_show = df_records[['Fecha', 'Estado', 'Causa', 'Justificada']]
        
        st.dataframe(df_to_show, use_container_width=True, hide_index=True)

    if st.button("Cerrar", key=f"close_total_detail_{student['id']}"):
        st.session_state.show_detail_dialog = False
        st.rerun()

# --- Aplicación Principal ---
def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_db()

    # --- Lógica de Login en la Barra Lateral ---
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    with st.sidebar:
        if st.session_state.logged_in:
            st.success(f"Sesión iniciada como **{st.session_state.username}**")
            st.info("La aplicación está en modo de edición.")
            if st.button("Cerrar Sesión"):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.rerun()
        else:
            st.info("Inicia sesión para registrar asistencias.")
            if not USER_CREDENTIALS:
                st.error("No hay usuarios de edición configurados. Contacta al administrador.")
            else:
                username = st.text_input("Usuario", key="login_user")
                password = st.text_input("Contraseña", type="password", key="login_pass")
                if st.button("Iniciar Sesión"):
                    if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
            st.warning("Sin iniciar sesión, solo puedes ver los datos.")

    # --- Contenido Principal de la Página ---
    st.title(APP_TITLE)
    st.markdown("Prácticas Profesionalizantes INDETEC - Colegio Técnico Antonio Martín Marte")

    if 'current_monday' not in st.session_state:
        st.session_state.current_monday = datetime.date(2025, 5, 26)

    nav_cols = st.columns([1, 2, 1])
    with nav_cols[0]:
        if st.button("⬅️ Semana Anterior"):
            st.session_state.current_monday -= datetime.timedelta(weeks=1)
            st.rerun()
    with nav_cols[2]:
        if st.button("Semana Siguiente ➡️"):
            st.session_state.current_monday += datetime.timedelta(weeks=1)
            st.rerun()

    current_monday = st.session_state.current_monday
    tuesday_obj, thursday_obj = get_week_days(current_monday)
    
    with nav_cols[1]:
        st.subheader(f"Semana del: {current_monday.strftime('%d/%m/%Y')} al {(current_monday + datetime.timedelta(days=6)).strftime('%d/%m/%Y')}")
    st.divider()

    students = get_students()
    if not students:
        st.warning("No hay estudiantes registrados.")
        return

    col_config = [2.5, 3, 3, 0.8] 
    header_cols = st.columns(col_config)
    header_cols[0].markdown("##### **Estudiante**")
    header_cols[1].markdown(f"##### **Martes ({tuesday_obj.strftime('%d/%m')})**")
    header_cols[2].markdown(f"##### **Jueves ({thursday_obj.strftime('%d/%m')})**")
    header_cols[3].markdown("##### **Total**")
    st.markdown("""<hr style="height:2px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
    
    is_read_only = not st.session_state.get('logged_in', False)

    for student in students:
        row_cols = st.columns(col_config)
        with row_cols[0]:
            st.markdown(f"**{student['nombre']}**")
        with row_cols[1]:
            render_attendance_cell(student['id'], student['nombre'], tuesday_obj, "tue", read_only=is_read_only)
        with row_cols[2]:
            render_attendance_cell(student['id'], student['nombre'], thursday_obj, "thu", read_only=is_read_only)
        with row_cols[3]:
            st.markdown('<div style="display: flex; justify-content: center; align-items: center; height: 100%;">', unsafe_allow_html=True)
            if st.button("👁️", key=f"detail_{student['id']}", help="Ver detalle total de asistencia"):
                st.session_state.show_detail_dialog = True
                st.session_state.detail_student_id = student['id']
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.divider()
        
    if st.session_state.get('show_detail_dialog') and st.session_state.get('detail_student_id'):
        selected_student_data = next((s for s in students if s['id'] == st.session_state.detail_student_id), None)
        if selected_student_data:
            show_total_student_detail_dialog(selected_student_data)

if __name__ == "__main__":
    main()
