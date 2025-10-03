# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
import tempfile

# Configuración de la página con colores personalizados
st.set_page_config(page_title="Sistema Integrado de Llantas", layout="wide", initial_sidebar_state="expanded")

# CSS personalizado para botones y resaltados
st.markdown("""
<style>
    .stButton>button {
        background-color: #2A2D62;
        color: white;
    }
    .stButton>button:hover {
        background-color: #F2B705;
        color: #2A2D62;
    }
    div[data-testid="stMarkdownContainer"] > p > strong {
        color: #2A2D62;
    }
</style>
""", unsafe_allow_html=True)

# Directorios para datos
if 'DATA_DIR' not in st.session_state:
    try:
        DATA_DIR = "data"
        os.makedirs(DATA_DIR, exist_ok=True)
        st.session_state['DATA_DIR'] = DATA_DIR
    except:
        DATA_DIR = tempfile.mkdtemp()
        st.session_state['DATA_DIR'] = DATA_DIR
else:
    DATA_DIR = st.session_state['DATA_DIR']

CLIENTES_FILE = os.path.join(DATA_DIR, "clientes.csv")
VEHICULOS_FILE = os.path.join(DATA_DIR, "vehiculos.csv")
LLANTAS_FILE = os.path.join(DATA_DIR, "llantas.csv")
SERVICIOS_FILE = os.path.join(DATA_DIR, "servicios.csv")
USUARIOS_FILE = os.path.join(DATA_DIR, "usuarios.csv")

# ============= FUNCIONES DE INICIALIZACIÓN =============
def inicializar_archivos():
    """Crea los archivos CSV si no existen"""
    if not os.path.exists(CLIENTES_FILE):
        pd.DataFrame(columns=['nit', 'nombre_cliente', 'frentes', 'fecha_creacion']).to_csv(CLIENTES_FILE, index=False, encoding='utf-8')
    
    if not os.path.exists(VEHICULOS_FILE):
        pd.DataFrame(columns=['nit_cliente', 'tipologia', 'placa_vehiculo', 'frente', 'fecha_creacion']).to_csv(VEHICULOS_FILE, index=False, encoding='utf-8')
    
    if not os.path.exists(LLANTAS_FILE):
        pd.DataFrame(columns=['id_llanta', 'nit_cliente', 'marca_llanta', 'referencia', 'dimension', 'disponibilidad', 'placa_vehiculo', 'pos_inicial', 'pos_final', 'estado_reencauche', 'reencauche1', 'reencauche2', 'reencauche3', 'reencauche4', 'vida', 'fecha_creacion', 'fecha_modificacion']).to_csv(LLANTAS_FILE, index=False, encoding='utf-8')
    
    if not os.path.exists(SERVICIOS_FILE):
        pd.DataFrame(columns=['id_servicio', 'fecha', 'id_llanta', 'placa_vehiculo', 'pos_inicial', 'pos_final', 'vida', 'tipologia', 'disponibilidad', 'kilometraje', 'rotacion', 'profundidad_1', 'profundidad_2', 'profundidad_3', 'balanceo', 'alineacion', 'regrabacion', 'torqueo', 'comentarios', 'usuario_registro', 'timestamp']).to_csv(SERVICIOS_FILE, index=False, encoding='utf-8')
    
    if not os.path.exists(USUARIOS_FILE):
        usuarios_default = pd.DataFrame([
            {'usuario': 'admin', 'password': 'admin123', 'nivel': 1, 'nombre': 'Administrador', 'clientes_asignados': ''},
            {'usuario': 'supervisor', 'password': 'super123', 'nivel': 2, 'nombre': 'Supervisor', 'clientes_asignados': ''},
            {'usuario': 'admin_cliente', 'password': 'cliente123', 'nivel': 4, 'nombre': 'Admin Cliente', 'clientes_asignados': ''},
            {'usuario': 'operario', 'password': 'oper123', 'nivel': 3, 'nombre': 'Operario', 'clientes_asignados': ''}
        ])
        usuarios_default.to_csv(USUARIOS_FILE, index=False, encoding='utf-8')

# ============= FUNCIONES AUXILIARES =============
def tiene_acceso_cliente(nit_cliente):
    """Verifica si el usuario tiene acceso al cliente especificado"""
    nivel = st.session_state.get('nivel', 999)
    
    if nivel in [1, 2, 3]:
        return True
    
    if nivel == 4:
        clientes_asignados = st.session_state.get('clientes_asignados', '')
        if clientes_asignados:
            lista_clientes = [c.strip() for c in clientes_asignados.split(',')]
            return nit_cliente in lista_clientes
        return False
    
    return False

def obtener_clientes_accesibles():
    """Retorna lista de NITs de clientes a los que el usuario tiene acceso"""
    nivel = st.session_state.get('nivel', 999)
    
    if nivel in [1, 2, 3]:
        df_clientes = pd.read_csv(CLIENTES_FILE, encoding='utf-8')
        return df_clientes['nit'].tolist() if not df_clientes.empty else []
    
    if nivel == 4:
        clientes_asignados = st.session_state.get('clientes_asignados', '')
        if clientes_asignados:
            return [c.strip() for c in clientes_asignados.split(',')]
    
    return []

def generar_id_servicio(nit_cliente, frente):
    """Genera el ID de servicio con formato: 2 letras cliente + letra frente + consecutivo"""
    df_clientes = pd.read_csv(CLIENTES_FILE, encoding='utf-8')
    df_servicios = pd.read_csv(SERVICIOS_FILE, encoding='utf-8')
    
    nombre_cliente = df_clientes[df_clientes['nit'] == nit_cliente]['nombre_cliente'].values[0]
    
    nombre_limpio = nombre_cliente.replace(" ", "")
    prefijo_cliente = nombre_limpio[:2].upper()
    
    if frente and frente != "General":
        prefijo_frente = frente[0].upper()
    else:
        prefijo_frente = ""
    
    prefijo = prefijo_cliente + prefijo_frente
    
    servicios_prefijo = df_servicios[df_servicios['id_servicio'].str.startswith(prefijo, na=False)]
    
    if servicios_prefijo.empty:
        consecutivo = 1
    else:
        try:
            numeros = servicios_prefijo['id_servicio'].str.extract(r'(\d+)$')[0].astype(int)
            consecutivo = numeros.max() + 1
        except:
            consecutivo = 1
    
    id_servicio = f"{prefijo}{consecutivo:04d}"
    
    return id_servicio

# ============= SISTEMA DE AUTENTICACIÓN =============
def login():
    """Sistema de login con niveles de usuario"""
    st.title("🔐 Sistema Integrado de Llantas")
    st.subheader("Inicio de Sesión")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Iniciar Sesión", use_container_width=True):
            df_usuarios = pd.read_csv(USUARIOS_FILE, encoding='utf-8')
            user_data = df_usuarios[(df_usuarios['usuario'] == usuario) & (df_usuarios['password'] == password)]
            
            if not user_data.empty:
                st.session_state['logged_in'] = True
                st.session_state['usuario'] = usuario
                st.session_state['nivel'] = int(user_data.iloc[0]['nivel'])
                st.session_state['nombre'] = user_data.iloc[0]['nombre']
                
                if 'clientes_asignados' in user_data.columns:
                    st.session_state['clientes_asignados'] = user_data.iloc[0]['clientes_asignados']
                else:
                    st.session_state['clientes_asignados'] = ''
                
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

def verificar_permiso(nivel_requerido):
    """Verifica si el usuario tiene el nivel necesario"""
    if st.session_state.get('nivel', 999) > nivel_requerido:
        st.error(f"⛔ No tienes permisos suficientes. Se requiere nivel {nivel_requerido} o superior.")
        return False
    return True

# ============= FUNCIÓN: SUBIR DATOS CSV =============
def subir_datos_csv():
    """Función para cargar datos desde archivos CSV usando append"""
    
    st.image("https://elchorroco.wordpress.com/wp-content/uploads/2025/10/megallanta-logo.png", width=200)
    st.header("📤 Subir Datos desde CSV")
    
    if not verificar_permiso(2):
        return
    
    st.subheader("Selecciona qué datos deseas cargar")
    
    tipo_dato = st.selectbox(
        "Tipo de Datos",
        options=["Clientes", "Vehículos", "Llantas", "Servicios"]
    )
    
    archivo = st.file_uploader(f"Subir archivo CSV de {tipo_dato}", type=['csv'])
    
    if archivo is not None:
        try:
            df_nuevo = pd.read_csv(archivo, encoding='utf-8')
            
            st.write("**Vista previa de los datos:**")
            st.dataframe(df_nuevo.head(), use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Confirmar y Agregar Datos", type="primary"):
                    # Leer datos existentes
                    if tipo_dato == "Clientes":
                        df_existente = pd.read_csv(CLIENTES_FILE, encoding='utf-8')
                        df_combinado = pd.concat([df_existente, df_nuevo], ignore_index=True)
                        df_combinado.to_csv(CLIENTES_FILE, index=False, encoding='utf-8')
                    elif tipo_dato == "Vehículos":
                        df_existente = pd.read_csv(VEHICULOS_FILE, encoding='utf-8')
                        df_combinado = pd.concat([df_existente, df_nuevo], ignore_index=True)
                        df_combinado.to_csv(VEHICULOS_FILE, index=False, encoding='utf-8')
                    elif tipo_dato == "Llantas":
                        df_existente = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
                        df_combinado = pd.concat([df_existente, df_nuevo], ignore_index=True)
                        df_combinado.to_csv(LLANTAS_FILE, index=False, encoding='utf-8')
                    elif tipo_dato == "Servicios":
                        df_existente = pd.read_csv(SERVICIOS_FILE, encoding='utf-8')
                        df_combinado = pd.concat([df_existente, df_nuevo], ignore_index=True)
                        df_combinado.to_csv(SERVICIOS_FILE, index=False, encoding='utf-8')
                    
                    st.success(f"✅ Datos de {tipo_dato} agregados exitosamente")
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancelar"):
                    st.rerun()
                    
        except Exception as e:
            st.error(f"Error al leer el archivo: {str(e)}")
            st.info("Asegúrate de que el CSV tenga las columnas correctas y esté codificado en UTF-8")

# ============= FUNCIÓN: ELIMINAR Y CORREGIR DATOS =============
def eliminar_corregir_datos():
    """Función para eliminar o corregir datos"""
    
    st.image("https://elchorroco.wordpress.com/wp-content/uploads/2025/10/megallanta-logo.png", width=200)
    st.header("✏️ Eliminar o Corregir Datos")
    
    if not verificar_permiso(2):
        return
    
    tab1, tab2, tab3, tab4 = st.tabs(["🚛 Vehículos", "⚙️ Llantas", "🛠️ Servicios", "👤 Clientes"])
    
    with tab1:
        st.subheader("Gestión de Vehículos")
        df_vehiculos = pd.read_csv(VEHICULOS_FILE, encoding='utf-8')
        
        if not df_vehiculos.empty:
            clientes_acceso = obtener_clientes_accesibles()
            df_vehiculos = df_vehiculos[df_vehiculos['nit_cliente'].isin(clientes_acceso)]
            
            if not df_vehiculos.empty:
                placa_editar = st.selectbox("Seleccionar Vehículo", df_vehiculos['placa_vehiculo'].values)
                
                vehiculo = df_vehiculos[df_vehiculos['placa_vehiculo'] == placa_editar].iloc[0]
                
                col1, col2 = st.columns(2)
                with col1:
                    nueva_tipologia = st.text_input("Tipología", value=vehiculo['tipologia'])
                    nuevo_frente = st.text_input("Frente", value=vehiculo['frente'])
                
                with col2:
                    if st.button("💾 Guardar Cambios", key="guardar_vehiculo"):
                        df_todos = pd.read_csv(VEHICULOS_FILE, encoding='utf-8')
                        df_todos.loc[df_todos['placa_vehiculo'] == placa_editar, 'tipologia'] = nueva_tipologia
                        df_todos.loc[df_todos['placa_vehiculo'] == placa_editar, 'frente'] = nuevo_frente
                        df_todos.to_csv(VEHICULOS_FILE, index=False, encoding='utf-8')
                        st.success("✅ Vehículo actualizado con éxito")
                        st.rerun()
                    
                    if st.button("🗑️ Eliminar Vehículo", key="eliminar_vehiculo"):
                        df_todos = pd.read_csv(VEHICULOS_FILE, encoding='utf-8')
                        df_todos = df_todos[df_todos['placa_vehiculo'] != placa_editar]
                        df_todos.to_csv(VEHICULOS_FILE, index=False, encoding='utf-8')
                        st.success("✅ Vehículo eliminado con éxito")
                        st.rerun()
            else:
                st.info("No tienes vehículos accesibles")
        else:
            st.info("No hay vehículos registrados")
    
    with tab2:
        st.subheader("Gestión de Llantas")
        df_llantas = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
        
        if not df_llantas.empty:
            clientes_acceso = obtener_clientes_accesibles()
            df_llantas = df_llantas[df_llantas['nit_cliente'].isin(clientes_acceso)]
            
            if not df_llantas.empty:
                id_editar = st.selectbox("Seleccionar Llanta", df_llantas['id_llanta'].values)
                
                llanta = df_llantas[df_llantas['id_llanta'] == id_editar].iloc[0]
                
                col1, col2 = st.columns(2)
                with col1:
                    nueva_marca = st.text_input("Marca", value=llanta.get('marca_llanta', ''))
                    nueva_referencia = st.text_input("Referencia", value=llanta.get('referencia', ''))
                
                with col2:
                    nueva_dimension = st.text_input("Dimensión", value=llanta.get('dimension', ''))
                
                if st.button("💾 Guardar Cambios", key="guardar_llanta"):
                    df_todos = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
                    df_todos.loc[df_todos['id_llanta'] == id_editar, 'marca_llanta'] = nueva_marca
                    df_todos.loc[df_todos['id_llanta'] == id_editar, 'referencia'] = nueva_referencia
                    df_todos.loc[df_todos['id_llanta'] == id_editar, 'dimension'] = nueva_dimension
                    df_todos.to_csv(LLANTAS_FILE, index=False, encoding='utf-8')
                    st.success("✅ Llanta actualizada con éxito")
                    st.rerun()
                
                if st.button("🗑️ Eliminar Llanta", key="eliminar_llanta"):
                    df_todos = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
                    df_todos = df_todos[df_todos['id_llanta'] != id_editar]
                    df_todos.to_csv(LLANTAS_FILE, index=False, encoding='utf-8')
                    st.success("✅ Llanta eliminada con éxito")
                    st.rerun()
            else:
                st.info("No tienes llantas accesibles")
        else:
            st.info("No hay llantas registradas")
    
    with tab3:
        st.subheader("Gestión de Servicios")
        df_servicios = pd.read_csv(SERVICIOS_FILE, encoding='utf-8')
        
        if not df_servicios.empty:
            id_servicio_editar = st.selectbox("Seleccionar Servicio", df_servicios['id_servicio'].values)
            
            if st.button("🗑️ Eliminar Servicio", key="eliminar_servicio"):
                df_servicios = df_servicios[df_servicios['id_servicio'] != id_servicio_editar]
                df_servicios.to_csv(SERVICIOS_FILE, index=False, encoding='utf-8')
                st.success("✅ Servicio eliminado con éxito")
                st.rerun()
        else:
            st.info("No hay servicios registrados")
    
    with tab4:
        st.subheader("Gestión de Clientes")
        
        if st.session_state.get('nivel') != 1:
            st.warning("⚠️ Solo el Administrador puede editar clientes")
            return
        
        df_clientes = pd.read_csv(CLIENTES_FILE, encoding='utf-8')
        
        if not df_clientes.empty:
            nit_editar = st.selectbox("Seleccionar Cliente", df_clientes['nit'].values)
            
            cliente = df_clientes[df_clientes['nit'] == nit_editar].iloc[0]
            
            nuevo_nombre = st.text_input("Nombre Cliente", value=cliente['nombre_cliente'])
            
            if st.button("💾 Guardar Cambios", key="guardar_cliente"):
                df_clientes.loc[df_clientes['nit'] == nit_editar, 'nombre_cliente'] = nuevo_nombre
                df_clientes.to_csv(CLIENTES_FILE, index=False, encoding='utf-8')
                st.success("✅ Cliente actualizado con éxito")
                st.rerun()
            
            if st.button("🗑️ Eliminar Cliente", key="eliminar_cliente"):
                df_clientes = df_clientes[df_clientes['nit'] != nit_editar]
                df_clientes.to_csv(CLIENTES_FILE, index=False, encoding='utf-8')
                st.success("✅ Cliente eliminado con éxito")
                st.rerun()
        else:
            st.info("No hay clientes registrados")

# ============= FUNCIÓN: LLANTAS DISPONIBLES =============
def ver_llantas_disponibles():
    """Función para ver todas las llantas y su disponibilidad"""
    
    st.image("https://elchorroco.wordpress.com/wp-content/uploads/2025/10/megallanta-logo.png", width=200)
    st.header("🔍 Estado de Llantas")
    
    df_llantas = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
    
    if df_llantas.empty:
        st.info("No hay llantas registradas")
        return
    
    clientes_acceso = obtener_clientes_accesibles()
    df_llantas = df_llantas[df_llantas['nit_cliente'].isin(clientes_acceso)]
    
    if df_llantas.empty:
        st.info("No tienes llantas accesibles")
        return
    
    tab1, tab2 = st.tabs(["📋 Ver Todas", "✅ Aprobar Reencauches"])
    
    with tab1:
        st.subheader("Inventario Completo de Llantas")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            opciones_disp = list(df_llantas['disponibilidad'].unique())
            opciones_disp.insert(0, "Todas")
            filtro_disp = st.selectbox("Filtrar por Disponibilidad", options=opciones_disp)
        
        if filtro_disp == "Todas":
            df_filtrado = df_llantas
        else:
            df_filtrado = df_llantas[df_llantas['disponibilidad'] == filtro_disp]
        
        columnas_mostrar = ['id_llanta', 'marca_llanta', 'referencia', 'dimension', 'disponibilidad', 'placa_vehiculo', 'pos_inicial', 'vida']
        for col in ['reencauche1', 'reencauche2', 'reencauche3', 'reencauche4']:
            if col in df_filtrado.columns:
                columnas_mostrar.append(col)
        
        st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True)
    
    with tab2:
        st.subheader("Aprobar Reencauches")
        
        if not verificar_permiso(2):
            return
        
        llantas_reencauche = df_llantas[
            (df_llantas['disponibilidad'] == 'reencauche') & 
            (df_llantas['estado_reencauche'] == 'condicionada_planta')
        ]
        
        if not llantas_reencauche.empty:
            # Aprobación masiva
            st.write("**Aprobación Masiva:**")
            marca_masiva = st.text_input("Marca para aprobación masiva (aplicará a todas)")
            if st.button("✅ Aprobar Todas", type="primary"):
                if not marca_masiva:
                    st.error("Debes ingresar la marca de reencauche")
                else:
                    df_todos = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
                    for idx, row in llantas_reencauche.iterrows():
                        vida_actual = int(row['vida']) if pd.notna(row['vida']) else 0
                        vida_nueva = vida_actual + 1
                        
                        if vida_nueva == 1:
                            df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'reencauche1'] = marca_masiva
                        elif vida_nueva == 2:
                            df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'reencauche2'] = marca_masiva
                        elif vida_nueva == 3:
                            df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'reencauche3'] = marca_masiva
                        elif vida_nueva == 4:
                            df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'reencauche4'] = marca_masiva
                        
                        df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'vida'] = vida_nueva
                        df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'estado_reencauche'] = 'aprobado'
                        df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'fecha_modificacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    df_todos.to_csv(LLANTAS_FILE, index=False, encoding='utf-8')
                    st.success(f"✅ {len(llantas_reencauche)} llantas aprobadas con marca: {marca_masiva}")
                    st.rerun()
            
            st.divider()
            st.write("**Aprobación Individual:**")
            
            # Lista para aprobación individual
            for idx, row in llantas_reencauche.iterrows():
                marca = row.get('marca_llanta', 'N/A')
                dimension = row.get('dimension', 'N/A')
                vida = row.get('vida', 0)
                
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**ID {row['id_llanta']}** - {marca} {dimension}")
                with col2:
                    marca_individual = st.text_input(f"Marca", key=f"marca_ind_{row['id_llanta']}", label_visibility="collapsed")
                with col3:
                    if st.button("Aprobar", key=f"aprobar_{row['id_llanta']}"):
                        if not marca_individual:
                            st.error("Ingresa la marca")
                        else:
                            df_todos = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
                            vida_nueva = int(vida) + 1
                            
                            if vida_nueva == 1:
                                df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'reencauche1'] = marca_individual
                            elif vida_nueva == 2:
                                df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'reencauche2'] = marca_individual
                            elif vida_nueva == 3:
                                df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'reencauche3'] = marca_individual
                            elif vida_nueva == 4:
                                df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'reencauche4'] = marca_individual
                            
                            df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'vida'] = vida_nueva
                            df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'estado_reencauche'] = 'aprobado'
                            df_todos.loc[df_todos['id_llanta'] == row['id_llanta'], 'fecha_modificacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            df_todos.to_csv(LLANTAS_FILE, index=False, encoding='utf-8')
                            st.success(f"✅ Llanta aprobada")
                            st.rerun()
        else:
            st.info("No hay llantas pendientes de aprobación")

# ============= FUNCIÓN 1: GESTIÓN DE CLIENTES =============
def crear_cliente():
    """Función para crear clientes con frentes"""
    
    st.image("https://elchorroco.wordpress.com/wp-content/uploads/2025/10/megallanta-logo.png", width=200)
    st.header("👤 Gestión de Clientes")
    
    if not verificar_permiso(2):
        return
    
    tab1, tab2 = st.tabs(["➕ Crear Cliente", "📋 Ver Clientes"])
    
    with tab1:
        st.subheader("Crear Nuevo Cliente")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nit = st.text_input("NIT (10 dígitos)", max_chars=10)
            nombre_cliente = st.text_input("Nombre del Cliente")
        
        with col2:
            num_frentes = st.number_input("Número de Frentes", min_value=0, max_value=20, value=1)
        
        frentes = []
        if num_frentes > 0:
            st.write("**Nombres de los Frentes:**")
            cols = st.columns(3)
            for i in range(num_frentes):
                with cols[i % 3]:
                    frente = st.text_input(f"Frente {i+1}", key=f"frente_{i}")
                    if frente:
                        frentes.append(frente)
        
        if st.button("💾 Guardar Cliente", type="primary"):
            if len(nit) != 10 or not nit.isdigit():
                st.error("El NIT debe tener exactamente 10 dígitos numéricos")
            elif not nombre_cliente:
                st.error("Debes ingresar el nombre del cliente")
            elif num_frentes > 0 and len(frentes) != num_frentes:
                st.error("Debes ingresar todos los nombres de frentes")
            else:
                df_clientes = pd.read_csv(CLIENTES_FILE, encoding='utf-8')
                
                if nit in df_clientes['nit'].values:
                    st.error("Este NIT ya está registrado")
                else:
                    nuevo_cliente = pd.DataFrame([{
                        'nit': nit,
                        'nombre_cliente': nombre_cliente,
                        'frentes': json.dumps(frentes) if frentes else json.dumps([]),
                        'fecha_creacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    
                    df_clientes = pd.concat([df_clientes, nuevo_cliente], ignore_index=True)
                    df_clientes.to_csv(CLIENTES_FILE, index=False, encoding='utf-8')
                    st.success("✅ Dato creado con éxito")
                    st.balloons()
                    st.rerun()
    
    with tab2:
        df_clientes = pd.read_csv(CLIENTES_FILE, encoding='utf-8')
        
        if st.session_state.get('nivel') == 4:
            clientes_acceso = obtener_clientes_accesibles()
            df_clientes = df_clientes[df_clientes['nit'].isin(clientes_acceso)]
        
        if not df_clientes.empty:
            for idx, row in df_clientes.iterrows():
                with st.expander(f"🏢 {row.get('nombre_cliente', 'N/A')} - NIT: {row.get('nit', 'N/A')}"):
                    frentes = json.loads(row.get('frentes', '[]')) if row.get('frentes') else []
                    if frentes:
                        st.write(f"**Frentes:** {', '.join(frentes)}")
                    else:
                        st.write("**Sin frentes**")
                    st.write(f"**Fecha de Creación:** {row.get('fecha_creacion', 'N/A')}")
        else:
            st.info("No hay clientes registrados o no tienes acceso")

# ============= FUNCIÓN 2: GESTIÓN DE VEHÍCULOS =============
def crear_vehiculos():
    """Función para crear vehículos asociados a cliente y frente"""
    
    st.image("https://elchorroco.wordpress.com/wp-content/uploads/2025/10/megallanta-logo.png", width=200)
    st.header("🚛 Gestión de Vehículos")
    
    if not verificar_permiso(2):
        return
    
    df_clientes = pd.read_csv(CLIENTES_FILE, encoding='utf-8')
    
    clientes_acceso = obtener_clientes_accesibles()
    df_clientes = df_clientes[df_clientes['nit'].isin(clientes_acceso)]
    
    if df_clientes.empty:
        st.warning("⚠️ Primero debes crear un cliente o no tienes acceso")
        return
    
    tab1, tab2 = st.tabs(["➕ Registrar Vehículo", "📋 Ver Vehículos"])
    
    with tab1:
        st.subheader("Registrar Nuevo Vehículo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cliente_seleccionado = st.selectbox(
                "Cliente",
                options=df_clientes['nit'].values,
                format_func=lambda x: f"{df_clientes[df_clientes['nit']==x]['nombre_cliente'].values[0]} - {x}"
            )
            
            frentes_cliente = json.loads(df_clientes[df_clientes['nit']==cliente_seleccionado]['frentes'].values[0])
            
            if frentes_cliente:
                frente = st.selectbox("Frente", options=frentes_cliente)
            else:
                frente = st.text_input("Frente (sin frentes definidos)", value="General")
        
        with col2:
            tipologia = st.selectbox("Tipología", ["Camión", "Tractomula", "Volqueta", "Turbo", "Sencillo", "Otro"])
            placa_vehiculo = st.text_input("Placa del Vehículo").upper()
        
        if st.button("💾 Registrar Vehículo", type="primary"):
            if not placa_vehiculo:
                st.error("Debes ingresar la placa del vehículo")
            else:
                df_vehiculos = pd.read_csv(VEHICULOS_FILE, encoding='utf-8')
                
                if placa_vehiculo in df_vehiculos['placa_vehiculo'].values:
                    st.error("Esta placa ya está registrada")
                else:
                    nuevo_vehiculo = pd.DataFrame([{
                        'nit_cliente': cliente_seleccionado,
                        'tipologia': tipologia,
                        'placa_vehiculo': placa_vehiculo,
                        'frente': frente,
                        'fecha_creacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    
                    df_vehiculos = pd.concat([df_vehiculos, nuevo_vehiculo], ignore_index=True)
                    df_vehiculos.to_csv(VEHICULOS_FILE, index=False, encoding='utf-8')
                    st.success("✅ Dato creado con éxito")
                    st.balloons()
                    st.rerun()
    
    with tab2:
        df_vehiculos = pd.read_csv(VEHICULOS_FILE, encoding='utf-8')
        
        df_vehiculos = df_vehiculos[df_vehiculos['nit_cliente'].isin(clientes_acceso)]
        
        if not df_vehiculos.empty:
            df_display = df_vehiculos.merge(df_clientes[['nit', 'nombre_cliente']], left_on='nit_cliente', right_on='nit')
            st.dataframe(df_display[['nombre_cliente', 'placa_vehiculo', 'tipologia', 'frente', 'fecha_creacion']], use_container_width=True)
        else:
            st.info("No hay vehículos registrados o no tienes acceso")

# ============= FUNCIÓN 3: GESTIÓN DE LLANTAS =============
def crear_llantas():
    """Función para crear llantas y asociarlas a clientes"""
    
    st.image("https://elchorroco.wordpress.com/wp-content/uploads/2025/10/megallanta-logo.png", width=200)
    st.header("⚙️ Gestión de Llantas")
    
    if not verificar_permiso(3):
        return
    
    df_clientes = pd.read_csv(CLIENTES_FILE, encoding='utf-8')
    
    clientes_acceso = obtener_clientes_accesibles()
    df_clientes = df_clientes[df_clientes['nit'].isin(clientes_acceso)]
    
    if df_clientes.empty:
        st.warning("⚠️ Primero debes crear un cliente o no tienes acceso")
        return
    
    tab1, tab2 = st.tabs(["➕ Registrar Llanta", "📋 Ver Llantas"])
    
    with tab1:
        st.subheader("Registrar Nueva Llanta")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cliente_seleccionado = st.selectbox(
                "Cliente",
                options=df_clientes['nit'].values,
                format_func=lambda x: f"{df_clientes[df_clientes['nit']==x]['nombre_cliente'].values[0]}",
                key="llanta_cliente"
            )
            marca_llanta = st.text_input("Marca de Llanta")
        
        with col2:
            referencia = st.text_input("Diseño (ej: XZA2)")
            dimension = st.text_input("Dimensión (ej: 295/80R22.5)")
        
        with col3:
            df_llantas = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
            max_id = df_llantas['id_llanta'].max() if not df_llantas.empty and 'id_llanta' in df_llantas.columns else 0
            id_llanta = st.number_input("ID Llanta", min_value=int(max_id)+1, value=int(max_id)+1)
        
        if st.button("💾 Registrar Llanta", type="primary"):
            if not dimension or not referencia or not marca_llanta:
                st.error("Debes completar todos los campos")
            else:
                df_llantas = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
                
                if id_llanta in df_llantas['id_llanta'].values:
                    st.error("Este ID de llanta ya existe")
                else:
                    nueva_llanta = pd.DataFrame([{
                        'id_llanta': id_llanta,
                        'nit_cliente': cliente_seleccionado,
                        'marca_llanta': marca_llanta,
                        'referencia': referencia,
                        'dimension': dimension,
                        'disponibilidad': 'llanta_nueva',
                        'placa_vehiculo': '',
                        'pos_inicial': '',
                        'pos_final': '',
                        'estado_reencauche': '',
                        'reencauche1': '',
                        'reencauche2': '',
                        'reencauche3': '',
                        'reencauche4': '',
                        'vida': 0,
                        'fecha_creacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'fecha_modificacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    
                    df_llantas = pd.concat([df_llantas, nueva_llanta], ignore_index=True)
                    df_llantas.to_csv(LLANTAS_FILE, index=False, encoding='utf-8')
                    st.success("✅ Dato creado con éxito")
                    st.balloons()
                    st.rerun()
    
    with tab2:
        df_llantas = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
        
        df_llantas = df_llantas[df_llantas['nit_cliente'].isin(clientes_acceso)]
        
        if not df_llantas.empty:
            df_display = df_llantas.merge(df_clientes[['nit', 'nombre_cliente']], left_on='nit_cliente', right_on='nit')
            columnas_mostrar = [col for col in ['id_llanta', 'nombre_cliente', 'marca_llanta', 'referencia', 'dimension', 'disponibilidad', 'placa_vehiculo', 'vida'] if col in df_display.columns]
            st.dataframe(df_display[columnas_mostrar], use_container_width=True)
        else:
            st.info("No hay llantas registradas o no tienes acceso")

# ============= FUNCIÓN 4: MONTAJE DE LLANTAS =============
def montaje_llantas():
    """Función para montar llantas en vehículos"""
    
    st.image("https://elchorroco.wordpress.com/wp-content/uploads/2025/10/megallanta-logo.png", width=200)
    st.header("🔧 Montaje de Llantas")
    
    if not verificar_permiso(3):
        return
    
    df_llantas = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
    df_vehiculos = pd.read_csv(VEHICULOS_FILE, encoding='utf-8')
    
    clientes_acceso = obtener_clientes_accesibles()
    df_llantas = df_llantas[df_llantas['nit_cliente'].isin(clientes_acceso)]
    df_vehiculos = df_vehiculos[df_vehiculos['nit_cliente'].isin(clientes_acceso)]
    
    if df_llantas.empty or df_vehiculos.empty:
        st.warning("⚠️ Debes tener llantas y vehículos registrados")
        return
    
    llantas_disponibles = df_llantas[
        (df_llantas['disponibilidad'].isin(['llanta_nueva', 'recambio'])) |
        ((df_llantas['disponibilidad'] == 'reencauche') & (df_llantas['estado_reencauche'] == 'aprobado'))
    ]
    
    if llantas_disponibles.empty:
        st.warning("⚠️ No hay llantas disponibles para montaje")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        id_llanta = st.selectbox(
            "Seleccionar Llanta",
            options=llantas_disponibles['id_llanta'].values,
            format_func=lambda x: f"ID {x} - {llantas_disponibles[llantas_disponibles['id_llanta']==x]['marca_llanta'].values[0]} {llantas_disponibles[llantas_disponibles['id_llanta']==x]['dimension'].values[0]}"
        )
    
    with col2:
        placa_vehiculo = st.selectbox(
            "Seleccionar Vehículo",
            options=df_vehiculos['placa_vehiculo'].values
        )
    
    with col3:
        posicion_inicial = st.text_input("Posición Inicial (ej: DI, DD, TI1, etc.)")
    
    if st.button("🔧 Montar Llanta", type="primary"):
        if not posicion_inicial:
            st.error("Debes especificar la posición inicial")
        else:
            df_llantas = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
            
            # Guardar pos_inicial solo si está vacío
            pos_inicial_actual = df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'pos_inicial'].values[0]
            if not pos_inicial_actual or pos_inicial_actual == '':
                df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'pos_inicial'] = posicion_inicial
            
            df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'disponibilidad'] = 'al_piso'
            df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'placa_vehiculo'] = placa_vehiculo
            df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'pos_final'] = posicion_inicial
            df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'estado_reencauche'] = ''
            df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'fecha_modificacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            df_llantas.to_csv(LLANTAS_FILE, index=False, encoding='utf-8')
            st.success(f"✅ Llanta ID {id_llanta} montada en vehículo {placa_vehiculo} - Posición: {posicion_inicial}")
            st.rerun()
    
    st.divider()
    st.subheader("📊 Llantas Montadas")
    llantas_montadas = df_llantas[df_llantas['disponibilidad'] == 'al_piso']
    if not llantas_montadas.empty:
        columnas_mostrar = [col for col in ['id_llanta', 'marca_llanta', 'dimension', 'placa_vehiculo', 'pos_inicial', 'pos_final', 'vida'] if col in llantas_montadas.columns]
        st.dataframe(llantas_montadas[columnas_mostrar], use_container_width=True)

# ============= FUNCIÓN 5: SERVICIOS =============
def registrar_servicios():
    """Función para registrar servicios de mantenimiento"""
    
    st.image("https://elchorroco.wordpress.com/wp-content/uploads/2025/10/megallanta-logo.png", width=200)
    st.header("🛠️ Registro de Servicios")
    
    if not verificar_permiso(3):
        return
    
    df_llantas = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
    df_vehiculos = pd.read_csv(VEHICULOS_FILE, encoding='utf-8')
    
    clientes_acceso = obtener_clientes_accesibles()
    df_llantas = df_llantas[df_llantas['nit_cliente'].isin(clientes_acceso)]
    
    llantas_en_piso = df_llantas[df_llantas['disponibilidad'] == 'al_piso']
    
    if llantas_en_piso.empty:
        st.warning("⚠️ No hay llantas montadas para registrar servicios")
        return
    
    st.subheader("Formulario de Servicio")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        id_llanta = st.selectbox(
            "ID Llanta",
            options=llantas_en_piso['id_llanta'].values,
            format_func=lambda x: f"ID {x} - Placa: {llantas_en_piso[llantas_en_piso['id_llanta']==x]['placa_vehiculo'].values[0]}"
        )
        
        fecha_servicio = st.date_input("Fecha del Servicio", datetime.now())
        kilometraje = st.number_input("Kilometraje", min_value=0, value=0)
    
    with col2:
        st.write("**Profundidades (mm)**")
        profundidad_1 = st.number_input("Profundidad 1", min_value=0.0, max_value=30.0, value=10.0, step=0.5)
        profundidad_2 = st.number_input("Profundidad 2", min_value=0.0, max_value=30.0, value=10.0, step=0.5)
        profundidad_3 = st.number_input("Profundidad 3", min_value=0.0, max_value=30.0, value=10.0, step=0.5)
    
    with col3:
        st.write("**Servicios Realizados**")
        rotacion = st.checkbox("Rotación")
        if rotacion:
            nueva_posicion = st.text_input("Nueva Posición")
        else:
            nueva_posicion = ""
        
        balanceo = st.checkbox("Balanceo")
        alineacion = st.checkbox("Alineación")
        regrabacion = st.checkbox("Regrabación")
        torqueo = st.checkbox("Torqueo")
    
    if st.button("💾 Registrar Servicio", type="primary"):
        if rotacion and not nueva_posicion:
            st.error("Si hay rotación, debes especificar la nueva posición")
        else:
            df_servicios = pd.read_csv(SERVICIOS_FILE, encoding='utf-8')
            df_llantas = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
            df_vehiculos = pd.read_csv(VEHICULOS_FILE, encoding='utf-8')
            
            llanta_data = df_llantas[df_llantas['id_llanta'] == id_llanta].iloc[0]
            placa = llanta_data['placa_vehiculo']
            nit_cliente = llanta_data['nit_cliente']
            pos_inicial = llanta_data.get('pos_inicial', '')
            vida = llanta_data.get('vida', 0)
            disponibilidad = llanta_data.get('disponibilidad', '')
            
            vehiculo_data = df_vehiculos[df_vehiculos['placa_vehiculo'] == placa].iloc[0]
            frente = vehiculo_data['frente']
            tipologia = vehiculo_data.get('tipologia', '')
            
            id_servicio = generar_id_servicio(nit_cliente, frente)
            
            pos_final_registro = nueva_posicion if rotacion and nueva_posicion else llanta_data.get('pos_final', '')
            
            if rotacion and nueva_posicion:
                df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'pos_final'] = nueva_posicion
                df_llantas.to_csv(LLANTAS_FILE, index=False, encoding='utf-8')
            
            nuevo_servicio = pd.DataFrame([{
                'id_servicio': id_servicio,
                'fecha': fecha_servicio.strftime("%d/%m/%Y"),
                'id_llanta': id_llanta,
                'placa_vehiculo': placa,
                'pos_inicial': pos_inicial,
                'vida': vida,
                'tipologia': tipologia,
                'disponibilidad': disponibilidad,
                'kilometraje': kilometraje,
                'rotacion': 'Sí' if rotacion else 'No',
                'pos_final': pos_final_registro,
                'profundidad_1': profundidad_1,
                'profundidad_2': profundidad_2,
                'profundidad_3': profundidad_3,
                'balanceo': 'Sí' if balanceo else 'No',
                'alineacion': 'Sí' if alineacion else 'No',
                'regrabacion': 'Sí' if regrabacion else 'No',
                'torqueo': 'Sí' if torqueo else 'No',
                'comentario_fvu': '',
                'usuario_registro': st.session_state['usuario'],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            
            df_servicios = pd.concat([df_servicios, nuevo_servicio], ignore_index=True)
            df_servicios.to_csv(SERVICIOS_FILE, index=False, encoding='utf-8')
            
            st.success(f"✅ Servicio {id_servicio} registrado exitosamente para llanta ID {id_llanta}")
            
            st.session_state['servicio_completado'] = True
            st.session_state['id_llanta_servicio'] = id_llanta
            st.rerun()
    
    if st.session_state.get('servicio_completado', False):
        st.divider()
        st.subheader("¿Qué deseas hacer ahora?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("➕ Registrar Otro Servicio", use_container_width=True):
                st.session_state['servicio_completado'] = False
                st.rerun()
        
        with col2:
            if st.button("🔽 Realizar Desmontaje", use_container_width=True, type="primary"):
                st.session_state['servicio_completado'] = False
                st.session_state['ir_a_desmontaje'] = True
                st.rerun()
    
    st.divider()
    st.subheader("📋 Historial de Servicios")
    df_servicios = pd.read_csv(SERVICIOS_FILE, encoding='utf-8')
    if not df_servicios.empty:
        servicios_recientes = df_servicios.sort_values('timestamp', ascending=False).head(10)
        columnas_mostrar = [col for col in ['id_servicio', 'fecha', 'id_llanta', 'placa_vehiculo', 'pos_inicial', 'vida', 'tipologia', 'kilometraje', 'profundidad_1', 'profundidad_2', 'profundidad_3'] if col in servicios_recientes.columns]
        st.dataframe(servicios_recientes[columnas_mostrar], use_container_width=True)

# ============= FUNCIÓN 6: DESMONTAJE =============
def desmontaje_llantas():
    """Función para desmontar llantas y cambiar disponibilidad"""
    
    st.image("https://elchorroco.wordpress.com/wp-content/uploads/2025/10/megallanta-logo.png", width=200)
    st.header("🔽 Desmontaje de Llantas")
    
    if not verificar_permiso(2):
        return
    
    df_llantas = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
    
    clientes_acceso = obtener_clientes_accesibles()
    df_llantas = df_llantas[df_llantas['nit_cliente'].isin(clientes_acceso)]
    
    llantas_montadas = df_llantas[df_llantas['disponibilidad'] == 'al_piso']
    
    if llantas_montadas.empty:
        st.warning("⚠️ No hay llantas montadas para desmontar")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        id_llanta = st.selectbox(
            "Seleccionar Llanta a Desmontar",
            options=llantas_montadas['id_llanta'].values,
            format_func=lambda x: f"ID {x} - Placa: {llantas_montadas[llantas_montadas['id_llanta']==x]['placa_vehiculo'].values[0]}"
        )
    
    with col2:
        nueva_disponibilidad = st.selectbox(
            "Nueva Disponibilidad",
            options=['recambio', 'reencauche', 'FVU']
        )
    
    razon_fvu = None
    if nueva_disponibilidad == 'FVU':
        razon_fvu = st.text_area("Razón de FVU (Fuera de Uso)")
    
    if st.button("🔽 Desmontar Llanta", type="primary"):
        if nueva_disponibilidad == 'FVU' and not razon_fvu:
            st.error("Debes especificar la razón del desecho")
        else:
            df_llantas = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
            df_servicios = pd.read_csv(SERVICIOS_FILE, encoding='utf-8')
            
            # Si es FVU, agregar comentario al último servicio
            if nueva_disponibilidad == 'FVU':
                servicios_llanta = df_servicios[df_servicios['id_llanta'] == id_llanta]
                if not servicios_llanta.empty:
                    ultimo_servicio_idx = df_servicios[df_servicios['id_llanta'] == id_llanta].index[-1]
                    df_servicios.loc[ultimo_servicio_idx, 'comentario_fvu'] = razon_fvu
                    df_servicios.to_csv(SERVICIOS_FILE, index=False, encoding='utf-8')
            
            df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'placa_vehiculo'] = ''
            # NO borrar pos_inicial, mantener el registro
            df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'fecha_modificacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if nueva_disponibilidad == 'reencauche':
                df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'disponibilidad'] = 'reencauche'
                df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'estado_reencauche'] = 'condicionada_planta'
                mensaje = f"✅ Llanta ID {id_llanta} desmontada. Estado: REENCAUCHE - Condicionada en planta"
            elif nueva_disponibilidad == 'FVU':
                df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'disponibilidad'] = 'FVU'
                df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'estado_reencauche'] = f"FVU: {razon_fvu}"
                mensaje = f"✅ Llanta ID {id_llanta} desmontada. Estado: FVU (Fuera de Uso)"
            else:
                df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'disponibilidad'] = 'recambio'
                df_llantas.loc[df_llantas['id_llanta'] == id_llanta, 'estado_reencauche'] = ''
                mensaje = f"✅ Llanta ID {id_llanta} desmontada. Estado: RECAMBIO (Disponible)"
            
            df_llantas.to_csv(LLANTAS_FILE, index=False, encoding='utf-8')
            st.success(mensaje)
            st.rerun()
    
    st.divider()
    st.subheader("✅ Aprobar Llantas de Reencauche")
    
    llantas_reencauche = df_llantas[
        (df_llantas['disponibilidad'] == 'reencauche') & 
        (df_llantas['estado_reencauche'] == 'condicionada_planta')
    ]
    
    if not llantas_reencauche.empty:
        for idx, row in llantas_reencauche.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                marca = row.get('marca_llanta', 'N/A')
                dimension = row.get('dimension', 'N/A')
                referencia = row.get('referencia', 'N/A')
                st.write(f"**ID {row['id_llanta']}** - {marca} {dimension} {referencia}")
            with col2:
                if st.button(f"Aprobar", key=f"aprobar_desm_{row['id_llanta']}"):
                    df_llantas.loc[df_llantas['id_llanta'] == row['id_llanta'], 'estado_reencauche'] = 'aprobado'
                    df_llantas.loc[df_llantas['id_llanta'] == row['id_llanta'], 'fecha_modificacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    df_llantas.to_csv(LLANTAS_FILE, index=False, encoding='utf-8')
                    st.success(f"Llanta ID {row['id_llanta']} aprobada para montaje")
                    st.rerun()
    else:
        st.info("No hay llantas pendientes de aprobación")

# ============= FUNCIÓN 7: REPORTES =============
def reportes():
    """Función para generar reportes y análisis"""
    
    st.image("https://elchorroco.wordpress.com/wp-content/uploads/2025/10/megallanta-logo.png", width=200)
    st.header("📊 Reportes y Análisis")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Desgaste de Llantas", "🛠️ Servicios por Llanta", "🚛 Servicios por Vehículo", "📊 Estado de Flota", "📥 Exportar Datos"])
    
    with tab1:
        st.subheader("Análisis de Desgaste")
        
        df_servicios = pd.read_csv(SERVICIOS_FILE, encoding='utf-8')
        
        if df_servicios.empty:
            st.info("No hay datos de servicios para analizar")
        else:
            col1, col2 = st.columns(2)
            with col1:
                filtro_llantas = st.multiselect(
                    "Filtrar Llantas",
                    options=['Todas'] + list(df_servicios['id_llanta'].unique()),
                    default=['Todas']
                )
            
            if 'Todas' in filtro_llantas:
                id_llanta_filtro = st.selectbox(
                    "Seleccionar Llanta para Análisis",
                    options=df_servicios['id_llanta'].unique()
                )
            else:
                id_llanta_filtro = st.selectbox(
                    "Seleccionar Llanta para Análisis",
                    options=filtro_llantas
                )
            
            servicios_llanta = df_servicios[df_servicios['id_llanta'] == id_llanta_filtro].sort_values('timestamp')
            
            if not servicios_llanta.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total de Servicios", len(servicios_llanta))
                    st.metric("Profundidad Promedio Actual", 
                             f"{servicios_llanta.iloc[-1][['profundidad_1', 'profundidad_2', 'profundidad_3']].mean():.2f} mm")
                
                with col2:
                    if len(servicios_llanta) > 1:
                        primera_prof = servicios_llanta.iloc[0][['profundidad_1', 'profundidad_2', 'profundidad_3']].mean()
                        ultima_prof = servicios_llanta.iloc[-1][['profundidad_1', 'profundidad_2', 'profundidad_3']].mean()
                        desgaste = primera_prof - ultima_prof
                        st.metric("Desgaste Total", f"{desgaste:.2f} mm")
                        
                        fecha_inicio = pd.to_datetime(servicios_llanta.iloc[0]['timestamp'])
                        fecha_fin = pd.to_datetime(servicios_llanta.iloc[-1]['timestamp'])
                        dias_uso = (fecha_fin - fecha_inicio).days
                        
                        if dias_uso > 0:
                            st.metric("Desgaste Promedio Diario", f"{desgaste/dias_uso:.3f} mm/día")
                
                st.divider()
                st.write("**Historial de Profundidades**")
                columnas_reporte = [col for col in ['id_servicio', 'fecha', 'kilometraje', 'profundidad_1', 'profundidad_2', 'profundidad_3', 'pos_final', 'comentario_fvu'] if col in servicios_llanta.columns]
                st.dataframe(servicios_llanta[columnas_reporte], use_container_width=True)
    
    with tab2:
        st.subheader("Servicios por Llanta")
        
        df_servicios = pd.read_csv(SERVICIOS_FILE, encoding='utf-8')
        
        if not df_servicios.empty:
            resumen = df_servicios.groupby('id_llanta').agg({
                'id_servicio': 'count',
                'rotacion': lambda x: (x == 'Sí').sum(),
                'balanceo': lambda x: (x == 'Sí').sum(),
                'alineacion': lambda x: (x == 'Sí').sum(),
                'regrabacion': lambda x: (x == 'Sí').sum(),
                'torqueo': lambda x: (x == 'Sí').sum()
            }).reset_index()
            
            resumen.columns = ['ID Llanta', 'Total Servicios', 'Rotaciones', 'Balanceos', 'Alineaciones', 'Regrabaciones', 'Torqueos']
            
            st.dataframe(resumen, use_container_width=True)
            
            st.divider()
            id_llanta_detalle = st.selectbox(
                "Ver Detalle de Llanta",
                options=df_servicios['id_llanta'].unique(),
                key="detalle_servicios"
            )
            
            servicios_detalle = df_servicios[df_servicios['id_llanta'] == id_llanta_detalle].sort_values('timestamp', ascending=False)
            st.dataframe(servicios_detalle, use_container_width=True)
        else:
            st.info("No hay servicios registrados")
    
    with tab3:
        st.subheader("Servicios por Vehículo")
        
        df_servicios = pd.read_csv(SERVICIOS_FILE, encoding='utf-8')
        
        if not df_servicios.empty:
            col1, col2 = st.columns(2)
            with col1:
                filtro_vehiculos = st.multiselect(
                    "Filtrar Vehículos",
                    options=['Todos'] + list(df_servicios['placa_vehiculo'].unique()),
                    default=['Todos']
                )
            
            if 'Todos' in filtro_vehiculos:
                vehiculo_filtro = st.selectbox(
                    "Seleccionar Vehículo",
                    options=df_servicios['placa_vehiculo'].unique()
                )
            else:
                vehiculo_filtro = st.selectbox(
                    "Seleccionar Vehículo",
                    options=filtro_vehiculos
                )
            
            servicios_vehiculo = df_servicios[df_servicios['placa_vehiculo'] == vehiculo_filtro].sort_values('timestamp', ascending=False)
            
            if not servicios_vehiculo.empty:
                st.metric("Total de Servicios en este Vehículo", len(servicios_vehiculo))
                
                st.divider()
                st.write("**Historial de Servicios**")
                columnas_vehiculo = [col for col in ['id_servicio', 'fecha', 'id_llanta', 'pos_inicial', 'vida', 'tipologia', 'kilometraje', 'profundidad_1', 'profundidad_2', 'profundidad_3'] if col in servicios_vehiculo.columns]
                st.dataframe(servicios_vehiculo[columnas_vehiculo], use_container_width=True)
        else:
            st.info("No hay servicios registrados")
    
    with tab4:
        st.subheader("Estado General de la Flota")
        
        df_llantas = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
        df_vehiculos = pd.read_csv(VEHICULOS_FILE, encoding='utf-8')
        
        clientes_acceso = obtener_clientes_accesibles()
        df_llantas = df_llantas[df_llantas['nit_cliente'].isin(clientes_acceso)]
        df_vehiculos = df_vehiculos[df_vehiculos['nit_cliente'].isin(clientes_acceso)]
        
        if not df_llantas.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Llantas", len(df_llantas))
            
            with col2:
                en_uso = len(df_llantas[df_llantas['disponibilidad'] == 'al_piso'])
                st.metric("Llantas en Uso", en_uso)
            
            with col3:
                disponibles = len(df_llantas[df_llantas['disponibilidad'].isin(['llanta_nueva', 'recambio'])])
                st.metric("Llantas Disponibles", disponibles)
            
            with col4:
                fvu = len(df_llantas[df_llantas['disponibilidad'] == 'FVU'])
                st.metric("Llantas FVU", fvu)
            
            st.divider()
            
            st.write("**Distribución por Estado**")
            estado_counts = df_llantas['disponibilidad'].value_counts()
            st.bar_chart(estado_counts)
            
            st.divider()
            
            st.write("**Llantas por Vehículo**")
            if not df_vehiculos.empty:
                vehiculos_con_llantas = df_llantas[df_llantas['placa_vehiculo'] != ''].groupby('placa_vehiculo').size().reset_index(name='cantidad_llantas')
                vehiculos_info = df_vehiculos.merge(vehiculos_con_llantas, on='placa_vehiculo', how='left')
                vehiculos_info['cantidad_llantas'].fillna(0, inplace=True)
                st.dataframe(vehiculos_info[['placa_vehiculo', 'tipologia', 'frente', 'cantidad_llantas']], use_container_width=True)
        else:
            st.info("No hay llantas registradas o no tienes acceso")
    
    with tab5:
        st.subheader("Exportar Datos")
        
        st.write("Descarga los datos en formato CSV para análisis externo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Descargar Servicios", use_container_width=True):
                df_servicios = pd.read_csv(SERVICIOS_FILE, encoding='utf-8')
                csv = df_servicios.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Servicios.csv",
                    data=csv,
                    file_name=f"servicios_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv'
                )
            
            if st.button("📥 Descargar Llantas", use_container_width=True):
                df_llantas = pd.read_csv(LLANTAS_FILE, encoding='utf-8')
                csv = df_llantas.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Llantas.csv",
                    data=csv,
                    file_name=f"llantas_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv'
                )
        
        with col2:
            if st.button("📥 Descargar Vehículos", use_container_width=True):
                df_vehiculos = pd.read_csv(VEHICULOS_FILE, encoding='utf-8')
                csv = df_vehiculos.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Vehiculos.csv",
                    data=csv,
                    file_name=f"vehiculos_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv'
                )
            
            if st.button("📥 Descargar Clientes", use_container_width=True):
                df_clientes = pd.read_csv(CLIENTES_FILE, encoding='utf-8')
                csv = df_clientes.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Clientes.csv",
                    data=csv,
                    file_name=f"clientes_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv'
                )
                
# ============= FUNCIÓN 8: GESTIÓN DE USUARIOS =============
def gestion_usuarios():
    """Función para gestionar usuarios (solo nivel 1)"""
    
    st.image("https://elchorroco.wordpress.com/wp-content/uploads/2025/10/megallanta-logo.png", width=200)
    st.header("👥 Gestión de Usuarios")
    
    if not verificar_permiso(1):
        return
    
    tab1, tab2 = st.tabs(["➕ Crear Usuario", "📋 Ver Usuarios"])
    
    with tab1:
        st.subheader("Crear Nuevo Usuario")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nuevo_usuario = st.text_input("Nombre de Usuario")
            nuevo_nombre = st.text_input("Nombre Completo")
        
        with col2:
            nueva_password = st.text_input("Contraseña", type="password")
            nuevo_nivel = st.selectbox("Nivel de Acceso", 
                                      options=[1, 2, 3, 4],
                                      format_func=lambda x: f"Nivel {x} - {'Administrador' if x==1 else 'Supervisor' if x==2 else 'Operario' if x==3 else 'Admin Cliente'}")
        
        clientes_seleccionados = ""
        if nuevo_nivel == 4:
            st.write("**Asignar Clientes (solo para Admin Cliente)**")
            df_clientes = pd.read_csv(CLIENTES_FILE, encoding='utf-8')
            if not df_clientes.empty:
                clientes_opciones = st.multiselect(
                    "Seleccionar Clientes",
                    options=df_clientes['nit'].values,
                    format_func=lambda x: f"{df_clientes[df_clientes['nit']==x]['nombre_cliente'].values[0]} - {x}"
                )
                clientes_seleccionados = ','.join(clientes_opciones)
        
        if st.button("💾 Crear Usuario", type="primary"):
            if not nuevo_usuario or not nueva_password or not nuevo_nombre:
                st.error("Debes completar todos los campos")
            elif nuevo_nivel == 4 and not clientes_seleccionados:
                st.error("Debes asignar al menos un cliente para Admin Cliente")
            else:
                df_usuarios = pd.read_csv(USUARIOS_FILE, encoding='utf-8')
                
                if nuevo_usuario in df_usuarios['usuario'].values:
                    st.error("Este nombre de usuario ya existe")
                else:
                    nuevo_user = pd.DataFrame([{
                        'usuario': nuevo_usuario,
                        'password': nueva_password,
                        'nivel': nuevo_nivel,
                        'nombre': nuevo_nombre,
                        'clientes_asignados': clientes_seleccionados
                    }])
                    
                    df_usuarios = pd.concat([df_usuarios, nuevo_user], ignore_index=True)
                    df_usuarios.to_csv(USUARIOS_FILE, index=False, encoding='utf-8')
                    st.success("✅ Dato creado con éxito")
                    st.balloons()
                    st.rerun()
    
    with tab2:
        df_usuarios = pd.read_csv(USUARIOS_FILE, encoding='utf-8')
        df_clientes = pd.read_csv(CLIENTES_FILE, encoding='utf-8')
        
        for idx, row in df_usuarios.iterrows():
            with st.expander(f"👤 {row.get('nombre', 'N/A')} - Nivel {row.get('nivel', 'N/A')}"):
                st.write(f"**Usuario:** {row.get('usuario', 'N/A')}")
                nivel = row.get('nivel', 0)
                st.write(f"**Nivel:** {nivel} - {'Administrador' if nivel==1 else 'Supervisor' if nivel==2 else 'Operario' if nivel==3 else 'Admin Cliente'}")
                
                if nivel == 4 and row.get('clientes_asignados'):
                    clientes_nits = row.get('clientes_asignados', '').split(',')
                    nombres_clientes = []
                    for nit in clientes_nits:
                        if nit and nit in df_clientes['nit'].values:
                            nombre = df_clientes[df_clientes['nit']==nit]['nombre_cliente'].values[0]
                            nombres_clientes.append(f"{nombre} ({nit})")
                    if nombres_clientes:
                        st.write(f"**Clientes Asignados:** {', '.join(nombres_clientes)}")
        
        st.info("""
        **Niveles de Usuario:**
        - **Nivel 1 (Administrador)**: Acceso total al sistema
        - **Nivel 2 (Supervisor)**: Gestión de clientes, vehículos, llantas y desmontajes
        - **Nivel 3 (Operario)**: Registro de servicios y montajes
        - **Nivel 4 (Admin Cliente)**: Administrador con acceso solo a clientes asignados
        """)

# ============= MENÚ PRINCIPAL =============
def main():
    """Función principal del sistema"""
    
    inicializar_archivos()
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if not st.session_state['logged_in']:
        login()
        return
    
    with st.sidebar:
        # Logo SILL
        st.image("https://elchorroco.wordpress.com/wp-content/uploads/2025/10/logo-sill.jpg", use_container_width=True)
        
        # Título en recuadro azul
        st.markdown("""
            <div style="background-color: #272F59; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                <h2 style="color: white; text-align: center; margin: 0;">Sistema Integrado de Llantas</h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.write(f"**Usuario:** {st.session_state['nombre']}")
        st.write(f"**Nivel:** {st.session_state['nivel']}")
        
        st.divider()
        
        st.subheader("¿Qué quieres hacer hoy?")
        
        opciones_menu = {
            "👤 Gestión de Clientes": "clientes",
            "🚛 Gestión de Vehículos": "vehiculos",
            "⚙️ Gestión de Llantas": "llantas",
            "🔍 Estado de Llantas": "estado_llantas",
            "🔧 Montaje de Llantas": "montaje",
            "🛠️ Registro de Servicios": "servicios",
            "🔽 Desmontaje de Llantas": "desmontaje",
            "📊 Reportes y Análisis": "reportes",
            "📤 Subir Datos CSV": "subir_csv",
            "✏️ Editar/Eliminar Datos": "editar_datos"
        }
        
        if st.session_state['nivel'] == 1:
            opciones_menu["👥 Gestión de Usuarios"] = "usuarios"
        
        opcion = st.radio("Menú Principal", list(opciones_menu.keys()), label_visibility="collapsed")
        
        st.divider()
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        st.divider()
        
        with st.expander("ℹ️ Información de Permisos"):
            if st.session_state['nivel'] == 1:
                st.success("✅ Acceso Total")
            elif st.session_state['nivel'] == 2:
                st.info("✅ Gestión y Supervisión\n❌ Gestión de Usuarios")
            elif st.session_state['nivel'] == 3:
                st.warning("✅ Operaciones\n❌ Gestión Administrativa")
            elif st.session_state['nivel'] == 4:
                st.info("✅ Administración de Clientes Asignados\n❌ Acceso a otros clientes")
        
        st.divider()
        
        # Marca de registro del programa
        logo_url = "https://elchorro.com.co/wp-content/uploads/2025/04/ch-plano.png?w=106&h=106"
        col_logo, col_texto = st.columns([1, 3], vertical_alignment="center")
        with col_logo:
            st.image(logo_url, width=60)
        with col_texto:
            st.markdown("""
                <div style="font-size:10px; line-height:1.1;">
                    <span style="font-style:italic;">Este programa fue desarrollado por:</span><br>
                    <span style="font-weight:bold;">Daniel Cortázar Triana</span><br>
                    <span style="font-weight:bold;">El Chorro Producciones SAS</span>
                </div>
            """, unsafe_allow_html=True)
    
    # Redirigir a desmontaje si se solicitó
    if st.session_state.get('ir_a_desmontaje', False):
        st.session_state['ir_a_desmontaje'] = False
        opcion = "🔽 Desmontaje de Llantas"
    
    # Contenido principal
    opcion_seleccionada = opciones_menu[opcion]
    
    if opcion_seleccionada == "clientes":
        crear_cliente()
    elif opcion_seleccionada == "vehiculos":
        crear_vehiculos()
    elif opcion_seleccionada == "llantas":
        crear_llantas()
    elif opcion_seleccionada == "estado_llantas":
        ver_llantas_disponibles()
    elif opcion_seleccionada == "montaje":
        montaje_llantas()
    elif opcion_seleccionada == "servicios":
        registrar_servicios()
    elif opcion_seleccionada == "desmontaje":
        desmontaje_llantas()
    elif opcion_seleccionada == "reportes":
        reportes()
    elif opcion_seleccionada == "subir_csv":
        subir_datos_csv()
    elif opcion_seleccionada == "editar_datos":
        eliminar_corregir_datos()
    elif opcion_seleccionada == "usuarios":
        gestion_usuarios()

if __name__ == "__main__":
    main()
