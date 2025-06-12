# Aplicación de Registro de Asistencia con Streamlit y SQLite

Esta aplicación permite llevar un registro de asistencia semanal para estudiantes. Utiliza Streamlit para la interfaz de usuario y SQLite para el almacenamiento de datos.

## Características

* Registro de asistencia (Presente, Ausente, Tarde) para los días martes y jueves.
* Registro de causa de inasistencia y si está justificada.
* Navegación entre semanas.
* Visualización detallada de la asistencia semanal por estudiante.
* Los datos se guardan automáticamente en una base de datos SQLite local (`asistencia.db`).

## Configuración y Ejecución Local

1.  **Prerrequisitos:**
    * Python 3.7 o superior.
    * `pip` (manejador de paquetes de Python).

2.  **Descargar los archivos:**
    * `app.py`
    * `requirements.txt`
    * (Este `README.md`)

3.  **Crear un entorno virtual (recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

4.  **Instalar dependencias:**
    Coloca el archivo `requirements.txt` en el mismo directorio que `app.py` y ejecuta:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Ejecutar la aplicación:**
    Asegúrate de estar en el directorio donde guardaste `app.py`.
    ```bash
    streamlit run app.py
    ```
    La aplicación se abrirá automáticamente en tu navegador web. La base de datos `asistencia.db` se creará en el mismo directorio la primera vez que se ejecute la aplicación.
