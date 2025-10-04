import pymysql
from datetime import datetime, timedelta
import numpy as np
from Back_end.Manejo_DB import ModeloPaciente, ModeloAutenticacion

class ModeloMetricas:
    """
    Modelo para calcular y obtener métricas de tiempos de espera entre 
    transiciones de estado en la atención de pacientes.
    """
    
    @classmethod
    def conectar(cls):
        """Establece conexión a la base de datos usando credenciales directas"""
        try:
            from Back_end.Manejo_DB import ModeloAutenticacion
            from Back_end.Manejo_DB import ModeloConfiguracion
            
            host_config = ModeloConfiguracion.cargar_configuracion()
            credenciales = ModeloAutenticacion.obtener_credenciales()
            return pymysql.connect(
                    host=host_config,
                    user=credenciales['usuario'],
                    password=credenciales['contrasena'],
                    database='sistema_visualizacion'
                )
        except Exception as e:
            print(f"Error de conexión a la base de datos: {str(e)}")
            return None
    
    @classmethod
    def calcular_estadisticas(cls, valores):
        """
        Calcula estadísticas descriptivas para una lista de valores.
        
        Args:
            valores (list): Lista de valores numéricos
            
        Returns:
            dict: Diccionario con promedio, mediana y percentil 90
        """
        if not valores or len(valores) == 0:
            return {
                'promedio': None,
                'mediana': None,
                'p90': None
            }
        
        try:
            # Usar numpy para calcular estadísticas
            valores_np = np.array(valores)
            return {
                'promedio': round(float(np.mean(valores_np)), 2),
                'mediana': round(float(np.median(valores_np)), 2),
                'p90': round(float(np.percentile(valores_np, 90)), 2)
            }
        except Exception as e:
            print(f"Error al calcular estadísticas: {str(e)}")
            return {
                'promedio': None,
                'mediana': None,
                'p90': None
            }
    
    @classmethod
    def obtener_metricas_triage(cls, area=None, fecha_inicio=None, fecha_fin=None, clase_triage=None):
        """
        Calcula las métricas de tiempo desde ingreso hasta triage.
        
        Args:
            area (str, opcional): Área para filtrar los datos
            fecha_inicio (str, opcional): Fecha de inicio del rango (formato: 'YYYY-MM-DD HH:MM:SS')
            fecha_fin (str, opcional): Fecha de fin del rango (formato: 'YYYY-MM-DD HH:MM:SS')
            clase_triage (str, opcional): Clase de triage para filtrar (1-5)
            
        Returns:
            dict: Diccionario con estadísticas de tiempo de triage
        """
        try:
            conn = cls.conectar()
            cursor = conn.cursor()
            
            # Construir condiciones del WHERE
            condiciones = []
            params = []
            
            # Solo considerar pacientes con triage realizado y timestamp de triage
            condiciones.append("triage IN ('1', '2', '3', '4', '5') AND triage_timestamp IS NOT NULL")
            
            if area:
                condiciones.append("ubicacion LIKE %s")
                params.append(f"%{area}%")
            
            if clase_triage:
                condiciones.append("triage = %s")
                params.append(clase_triage)
            
            if fecha_inicio:
                condiciones.append("ingreso >= %s")
                params.append(fecha_inicio)
                
            if fecha_fin:
                condiciones.append("ingreso <= %s")
                params.append(fecha_fin)
            
            # Construir la consulta
            query = """
                SELECT 
                    TIMESTAMPDIFF(MINUTE, ingreso, triage_timestamp) as tiempo_triage
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones)
            
            # Ejecutar consulta
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            
            # Extraer tiempos
            tiempos = [resultado[0] for resultado in resultados if resultado[0] is not None]
            
            # Calcular estadísticas
            estadisticas = cls.calcular_estadisticas(tiempos)
            
            conn.close()
            return {
                'total_pacientes': len(tiempos),
                'estadisticas': estadisticas
            }
            
        except Exception as e:
            print(f"Error al obtener métricas de triage: {str(e)}")
            return {
                'total_pacientes': 0,
                'estadisticas': {
                    'promedio': None,
                    'mediana': None,
                    'p90': None
                }
            }
    
    @classmethod
    def obtener_metricas_consulta_ingreso(cls, area=None, fecha_inicio=None, fecha_fin=None, clase_triage=None):
        """
        Calcula las métricas de tiempo desde CI no realizado hasta CI realizado.
        
        Args:
            area (str, opcional): Área para filtrar los datos
            fecha_inicio (str, opcional): Fecha de inicio del rango
            fecha_fin (str, opcional): Fecha de fin del rango
            clase_triage (str, opcional): Clase de triage para filtrar (1-5)
            
        Returns:
            dict: Diccionario con estadísticas de tiempo de consulta de ingreso
        """
        try:
            conn = cls.conectar()
            cursor = conn.cursor()
            
            # Construir condiciones del WHERE
            condiciones = []
            params = []
            
            # Solo considerar pacientes con CI realizado y timestamps correspondientes
            condiciones.append("ci = 'Realizado' AND ci_no_realizado_timestamp IS NOT NULL AND ci_realizado_timestamp IS NOT NULL")
            
            if area:
                condiciones.append("ubicacion LIKE %s")
                params.append(f"%{area}%")
            
            if clase_triage:
                condiciones.append("triage = %s")
                params.append(clase_triage)
            
            if fecha_inicio:
                condiciones.append("ingreso >= %s")
                params.append(fecha_inicio)
                
            if fecha_fin:
                condiciones.append("ingreso <= %s")
                params.append(fecha_fin)
            
            # Construir la consulta
            query = """
                SELECT 
                    TIMESTAMPDIFF(MINUTE, ci_no_realizado_timestamp, ci_realizado_timestamp) as tiempo_ci
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones)
            
            # Ejecutar consulta
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            
            # Extraer tiempos
            tiempos = [resultado[0] for resultado in resultados if resultado[0] is not None]
            
            # Calcular estadísticas
            estadisticas = cls.calcular_estadisticas(tiempos)
            
            conn.close()
            return {
                'total_pacientes': len(tiempos),
                'estadisticas': estadisticas
            }
            
        except Exception as e:
            print(f"Error al obtener métricas de consulta de ingreso: {str(e)}")
            return {
                'total_pacientes': 0,
                'estadisticas': {
                    'promedio': None,
                    'mediana': None,
                    'p90': None
                }
            }
            

    @classmethod
    def obtener_metricas_laboratorios(cls, area=None, fecha_inicio=None, fecha_fin=None, clase_triage=None):
        """
        Calcula las métricas de tiempo para laboratorios, incluyendo:
        - Tiempo desde "No realizado" hasta "En espera de resultados"
        - Tiempo desde "En espera de resultados" hasta "Resultados completos"
        - Tiempo total desde "No realizado" hasta "Resultados completos"
        
        Args:
            area (str, opcional): Área para filtrar los datos
            fecha_inicio (str, opcional): Fecha de inicio del rango
            fecha_fin (str, opcional): Fecha de fin del rango
            clase_triage (str, opcional): Clase de triage para filtrar (1-5)
            
        Returns:
            dict: Diccionario con estadísticas de tiempo de procesamiento de laboratorios
        """
        try:
            conn = cls.conectar()
            cursor = conn.cursor()
            
            # Base conditions for filtering
            condiciones_base = []
            params_base = []
            
            if area:
                condiciones_base.append("ubicacion LIKE %s")
                params_base.append(f"%{area}%")
            
            if clase_triage:
                condiciones_base.append("triage = %s")
                params_base.append(clase_triage)
            
            if fecha_inicio:
                condiciones_base.append("ingreso >= %s")
                params_base.append(fecha_inicio)
                
            if fecha_fin:
                condiciones_base.append("ingreso <= %s")
                params_base.append(fecha_fin)
            
            # Resultados para diferentes transiciones
            resultados = {}
            
            # 1. Métricas para "No realizado" a "En espera de resultados"
            condiciones_solicitud = condiciones_base.copy()
            params_solicitud = params_base.copy()
            condiciones_solicitud.append(
                "labs IN ('En espera de resultados', 'Resultados completos') AND labs_no_realizado_timestamp IS NOT NULL AND labs_solicitados_timestamp IS NOT NULL"
            )
            
            query_solicitud = """
                SELECT 
                    TIMESTAMPDIFF(MINUTE, labs_no_realizado_timestamp, labs_solicitados_timestamp) as tiempo_solicitud
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones_solicitud)
            
            cursor.execute(query_solicitud, params_solicitud)
            resultados_solicitud = cursor.fetchall()
            tiempos_solicitud = [r[0] for r in resultados_solicitud if r[0] is not None]
            
            # 2. Métricas para "En espera de resultados" a "Resultados completos"
            condiciones_resultados = condiciones_base.copy()
            params_resultados = params_base.copy()
            condiciones_resultados.append(
                "labs = 'Resultados completos' AND labs_solicitados_timestamp IS NOT NULL AND labs_completos_timestamp IS NOT NULL"
            )
            
            query_resultados = """
                SELECT 
                    TIMESTAMPDIFF(MINUTE, labs_solicitados_timestamp, labs_completos_timestamp) as tiempo_resultados
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones_resultados)
            
            cursor.execute(query_resultados, params_resultados)
            resultados_resultados = cursor.fetchall()
            tiempos_resultados = [r[0] for r in resultados_resultados if r[0] is not None]
            
            # 3. Métricas para tiempo total
            condiciones_total = condiciones_base.copy()
            params_total = params_base.copy()
            condiciones_total.append(
                "labs = 'Resultados completos' AND labs_no_realizado_timestamp IS NOT NULL AND labs_completos_timestamp IS NOT NULL"
            )
            
            query_total = """
                SELECT 
                    TIMESTAMPDIFF(MINUTE, labs_no_realizado_timestamp, labs_completos_timestamp) as tiempo_total
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones_total)
            
            cursor.execute(query_total, params_total)
            resultados_total = cursor.fetchall()
            tiempos_total = [r[0] for r in resultados_total if r[0] is not None]
            
            # Calcular estadísticas para cada conjunto
            estadisticas_solicitud = cls.calcular_estadisticas(tiempos_solicitud)
            estadisticas_resultados = cls.calcular_estadisticas(tiempos_resultados)
            estadisticas_total = cls.calcular_estadisticas(tiempos_total)
            
            conn.close()
            return {
                'total_pacientes_solicitud': len(tiempos_solicitud),
                'estadisticas_solicitud': estadisticas_solicitud,
                'total_pacientes_resultados': len(tiempos_resultados),
                'estadisticas_resultados': estadisticas_resultados,
                'total_pacientes_total': len(tiempos_total),
                'estadisticas_total': estadisticas_total
            }
            
        except Exception as e:
            print(f"Error al obtener métricas de laboratorios: {str(e)}")
            return {
                'total_pacientes_solicitud': 0,
                'estadisticas_solicitud': {'promedio': None, 'mediana': None, 'p90': None},
                'total_pacientes_resultados': 0,
                'estadisticas_resultados': {'promedio': None, 'mediana': None, 'p90': None},
                'total_pacientes_total': 0,
                'estadisticas_total': {'promedio': None, 'mediana': None, 'p90': None}
            }

    @classmethod
    def obtener_metricas_imagenes(cls, area=None, fecha_inicio=None, fecha_fin=None, clase_triage=None):
        """
        Calcula las métricas de tiempo para imágenes diagnósticas, incluyendo:
        - Tiempo desde "No realizado" hasta "En espera de resultados"
        - Tiempo desde "En espera de resultados" hasta "Resultados completos"
        - Tiempo total desde "No realizado" hasta "Resultados completos"
        
        Args:
            area (str, opcional): Área para filtrar los datos
            fecha_inicio (str, opcional): Fecha de inicio del rango
            fecha_fin (str, opcional): Fecha de fin del rango
            clase_triage (str, opcional): Clase de triage para filtrar (1-5)
            
        Returns:
            dict: Diccionario con estadísticas de tiempo de procesamiento de imágenes
        """
        try:
            conn = cls.conectar()
            cursor = conn.cursor()
            
            # Base conditions for filtering
            condiciones_base = []
            params_base = []
            
            if area:
                condiciones_base.append("ubicacion LIKE %s")
                params_base.append(f"%{area}%")
            
            if clase_triage:
                condiciones_base.append("triage = %s")
                params_base.append(clase_triage)
            
            if fecha_inicio:
                condiciones_base.append("ingreso >= %s")
                params_base.append(fecha_inicio)
                
            if fecha_fin:
                condiciones_base.append("ingreso <= %s")
                params_base.append(fecha_fin)
            
            # Resultados para diferentes transiciones
            resultados = {}
            
            # 1. Métricas para "No realizado" a "En espera de resultados"
            condiciones_solicitud = condiciones_base.copy()
            params_solicitud = params_base.copy()
            condiciones_solicitud.append(
                "ix IN ('En espera de resultados', 'Resultados completos') AND ix_no_realizado_timestamp IS NOT NULL AND ix_solicitados_timestamp IS NOT NULL"
            )
            
            query_solicitud = """
                SELECT 
                    TIMESTAMPDIFF(MINUTE, ix_no_realizado_timestamp, ix_solicitados_timestamp) as tiempo_solicitud
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones_solicitud)
            
            cursor.execute(query_solicitud, params_solicitud)
            resultados_solicitud = cursor.fetchall()
            tiempos_solicitud = [r[0] for r in resultados_solicitud if r[0] is not None]
            
            # 2. Métricas para "En espera de resultados" a "Resultados completos"
            condiciones_resultados = condiciones_base.copy()
            params_resultados = params_base.copy()
            condiciones_resultados.append(
                "ix = 'Resultados completos' AND ix_solicitados_timestamp IS NOT NULL AND ix_completos_timestamp IS NOT NULL"
            )
            
            query_resultados = """
                SELECT 
                    TIMESTAMPDIFF(MINUTE, ix_solicitados_timestamp, ix_completos_timestamp) as tiempo_resultados
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones_resultados)
            
            cursor.execute(query_resultados, params_resultados)
            resultados_resultados = cursor.fetchall()
            tiempos_resultados = [r[0] for r in resultados_resultados if r[0] is not None]
            
            # 3. Métricas para tiempo total
            condiciones_total = condiciones_base.copy()
            params_total = params_base.copy()
            condiciones_total.append(
                "ix = 'Resultados completos' AND ix_no_realizado_timestamp IS NOT NULL AND ix_completos_timestamp IS NOT NULL"
            )
            
            query_total = """
                SELECT 
                    TIMESTAMPDIFF(MINUTE, ix_no_realizado_timestamp, ix_completos_timestamp) as tiempo_total
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones_total)
            
            cursor.execute(query_total, params_total)
            resultados_total = cursor.fetchall()
            tiempos_total = [r[0] for r in resultados_total if r[0] is not None]
            
            # Calcular estadísticas para cada conjunto
            estadisticas_solicitud = cls.calcular_estadisticas(tiempos_solicitud)
            estadisticas_resultados = cls.calcular_estadisticas(tiempos_resultados)
            estadisticas_total = cls.calcular_estadisticas(tiempos_total)
            
            conn.close()
            return {
                'total_pacientes_solicitud': len(tiempos_solicitud),
                'estadisticas_solicitud': estadisticas_solicitud,
                'total_pacientes_resultados': len(tiempos_resultados),
                'estadisticas_resultados': estadisticas_resultados,
                'total_pacientes_total': len(tiempos_total),
                'estadisticas_total': estadisticas_total
            }
            
        except Exception as e:
            print(f"Error al obtener métricas de imágenes diagnósticas: {str(e)}")
            return {
                'total_pacientes_solicitud': 0,
                'estadisticas_solicitud': {'promedio': None, 'mediana': None, 'p90': None},
                'total_pacientes_resultados': 0,
                'estadisticas_resultados': {'promedio': None, 'mediana': None, 'p90': None},
                'total_pacientes_total': 0,
                'estadisticas_total': {'promedio': None, 'mediana': None, 'p90': None}
            }
   
    @classmethod
    def obtener_metricas_interconsulta(cls, area=None, fecha_inicio=None, fecha_fin=None, clase_triage=None):
        """
        Calcula las métricas de tiempo para interconsultas, tanto para apertura como para realización.
        
        Args:
            area (str, opcional): Área para filtrar los datos
            fecha_inicio (str, opcional): Fecha de inicio del rango
            fecha_fin (str, opcional): Fecha de fin del rango
            clase_triage (str, opcional): Clase de triage para filtrar (1-5)
            
        Returns:
            dict: Diccionario con estadísticas de tiempo para interconsultas
        """
        try:
            conn = cls.conectar()
            cursor = conn.cursor()
            
            # Construir condiciones del WHERE
            condiciones = []
            params = []
            
            # Solo considerar pacientes con interconsulta realizada y timestamps correspondientes
            condiciones.append("inter = 'Realizada' AND inter_no_abierta_timestamp IS NOT NULL AND inter_abierta_timestamp IS NOT NULL AND inter_realizada_timestamp IS NOT NULL")
            
            if area:
                condiciones.append("ubicacion LIKE %s")
                params.append(f"%{area}%")
            
            if clase_triage:
                condiciones.append("triage = %s")
                params.append(clase_triage)
            
            if fecha_inicio:
                condiciones.append("ingreso >= %s")
                params.append(fecha_inicio)
                
            if fecha_fin:
                condiciones.append("ingreso <= %s")
                params.append(fecha_fin)
            
            # Construir la consulta para tiempo de apertura (no abierta -> abierta)
            query_apertura = """
                SELECT 
                    TIMESTAMPDIFF(MINUTE, inter_no_abierta_timestamp, inter_abierta_timestamp) as tiempo_apertura
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones)
            
            # Ejecutar consulta de tiempo de apertura
            cursor.execute(query_apertura, params)
            resultados_apertura = cursor.fetchall()
            
            # Extraer tiempos de apertura
            tiempos_apertura = [resultado[0] for resultado in resultados_apertura if resultado[0] is not None]
            
            # Construir la consulta para tiempo de realización (abierta -> realizada)
            query_realizacion = """
                SELECT 
                    TIMESTAMPDIFF(MINUTE, inter_abierta_timestamp, inter_realizada_timestamp) as tiempo_realizacion
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones)
            
            # Ejecutar consulta de tiempo de realización
            cursor.execute(query_realizacion, params)
            resultados_realizacion = cursor.fetchall()
            
            # Extraer tiempos de realización
            tiempos_realizacion = [resultado[0] for resultado in resultados_realizacion if resultado[0] is not None]
            
            # Construir la consulta para tiempo total (no abierta -> realizada)
            query_total = """
                SELECT 
                    TIMESTAMPDIFF(MINUTE, inter_no_abierta_timestamp, inter_realizada_timestamp) as tiempo_total
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones)
            
            # Ejecutar consulta de tiempo total
            cursor.execute(query_total, params)
            resultados_total = cursor.fetchall()
            
            # Extraer tiempos totales
            tiempos_total = [resultado[0] for resultado in resultados_total if resultado[0] is not None]
            
            # Calcular estadísticas para cada conjunto de tiempos
            estadisticas_apertura = cls.calcular_estadisticas(tiempos_apertura)
            estadisticas_realizacion = cls.calcular_estadisticas(tiempos_realizacion)
            estadisticas_total = cls.calcular_estadisticas(tiempos_total)
            
            conn.close()
            return {
                'total_pacientes': len(tiempos_total),
                'estadisticas_apertura': estadisticas_apertura,
                'estadisticas_realizacion': estadisticas_realizacion,
                'estadisticas_total': estadisticas_total
            }
            
        except Exception as e:
            print(f"Error al obtener métricas de interconsulta: {str(e)}")
            return {
                'total_pacientes': 0,
                'estadisticas_apertura': {
                    'promedio': None,
                    'mediana': None,
                    'p90': None
                },
                'estadisticas_realizacion': {
                    'promedio': None,
                    'mediana': None,
                    'p90': None
                },
                'estadisticas_total': {
                    'promedio': None,
                    'mediana': None,
                    'p90': None
                }
            }

    @classmethod
    def obtener_metricas_rv(cls, area=None, fecha_inicio=None, fecha_fin=None, clase_triage=None):
        """
        Calcula las métricas de tiempo desde RV no realizado hasta RV realizado.
        
        Args:
            area (str, opcional): Área para filtrar los datos
            fecha_inicio (str, opcional): Fecha de inicio del rango
            fecha_fin (str, opcional): Fecha de fin del rango
            clase_triage (str, opcional): Clase de triage para filtrar (1-5)
            
        Returns:
            dict: Diccionario con estadísticas de tiempo de revaloración
        """
        try:
            conn = cls.conectar()
            cursor = conn.cursor()
            
            # Construir condiciones del WHERE
            condiciones = []
            params = []
            
            # Solo considerar pacientes con RV realizado y timestamps correspondientes
            condiciones.append("rv = 'Realizado' AND rv_no_realizado_timestamp IS NOT NULL AND rv_realizado_timestamp IS NOT NULL")
            
            if area:
                condiciones.append("ubicacion LIKE %s")
                params.append(f"%{area}%")
            
            if clase_triage:
                condiciones.append("triage = %s")
                params.append(clase_triage)
            
            if fecha_inicio:
                condiciones.append("ingreso >= %s")
                params.append(fecha_inicio)
                
            if fecha_fin:
                condiciones.append("ingreso <= %s")
                params.append(fecha_fin)
            
            # Construir la consulta
            query = """
                SELECT 
                    TIMESTAMPDIFF(MINUTE, rv_no_realizado_timestamp, rv_realizado_timestamp) as tiempo_rv
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones)
            
            # Ejecutar consulta
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            
            # Extraer tiempos
            tiempos = [resultado[0] for resultado in resultados if resultado[0] is not None]
            
            # Calcular estadísticas
            estadisticas = cls.calcular_estadisticas(tiempos)
            
            conn.close()
            return {
                'total_pacientes': len(tiempos),
                'estadisticas': estadisticas
            }
            
        except Exception as e:
            print(f"Error al obtener métricas de revaloración: {str(e)}")
            return {
                'total_pacientes': 0,
                'estadisticas': {
                    'promedio': None,
                    'mediana': None,
                    'p90': None
                }
            }

    @classmethod
    def obtener_metricas_tiempo_total(cls, area=None, fecha_inicio=None, fecha_fin=None, clase_triage=None):
        """
        Calcula las métricas de tiempo total de atención desde ingreso hasta alta o último timestamp disponible.
        
        Args:
            area (str, opcional): Área para filtrar los datos
            fecha_inicio (str, opcional): Fecha de inicio del rango
            fecha_fin (str, opcional): Fecha de fin del rango
            clase_triage (str, opcional): Clase de triage para filtrar (1-5)
            
        Returns:
            dict: Diccionario con estadísticas de tiempo total de atención
        """
        try:
            conn = cls.conectar()
            cursor = conn.cursor()
            
            # Construir condiciones del WHERE
            condiciones = []
            params = []
            
            # Considerar solo pacientes con alta o con algún timestamp final
            condiciones.append("""
                (
                    (conducta = 'De Alta' AND alta_timestamp IS NOT NULL) OR
                    ci_realizado_timestamp IS NOT NULL OR 
                    labs_completos_timestamp IS NOT NULL OR 
                    ix_completos_timestamp IS NOT NULL OR 
                    inter_realizada_timestamp IS NOT NULL OR 
                    rv_realizado_timestamp IS NOT NULL
                )
            """)
            
            if area:
                condiciones.append("ubicacion LIKE %s")
                params.append(f"%{area}%")
            
            if clase_triage:
                condiciones.append("triage = %s")
                params.append(clase_triage)
            
            if fecha_inicio:
                condiciones.append("ingreso >= %s")
                params.append(fecha_inicio)
                
            if fecha_fin:
                condiciones.append("ingreso <= %s")
                params.append(fecha_fin)
            
            # Ejecutar consulta usando GREATEST() para seleccionar el timestamp más reciente
            query = """
                SELECT 
                    TIMESTAMPDIFF(MINUTE, ingreso, 
                        GREATEST(
                            COALESCE(alta_timestamp, '1000-01-01'),
                            COALESCE(observacion_timestamp, '1000-01-01'),
                            COALESCE(rv_realizado_timestamp, '1000-01-01')
                        )
                    ) as tiempo_total
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones)
            
            # Ejecutar consulta
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            
            # Extraer tiempos válidos (mayores que 0)
            tiempos = [resultado[0] for resultado in resultados if resultado[0] is not None and resultado[0] > 0]
            
            # Calcular estadísticas
            estadisticas = cls.calcular_estadisticas(tiempos)
            
            # Calcular métricas adicionales específicas por conducta
            metricas_por_conducta = {}
            
            # Calcular tiempos para pacientes dados de alta
            query_alta = query.replace(
                " AND ".join(condiciones),
                " AND ".join(condiciones + ["conducta = 'De Alta'"])
            )
            cursor.execute(query_alta, params)
            resultados_alta = cursor.fetchall()
            tiempos_alta = [r[0] for r in resultados_alta if r[0] is not None and r[0] > 0]
            metricas_por_conducta['alta'] = {
                'total': len(tiempos_alta),
                'estadisticas': cls.calcular_estadisticas(tiempos_alta)
            }
            
            # Calcular tiempos para pacientes en observación
            query_observacion = query.replace(
                " AND ".join(condiciones),
                " AND ".join(condiciones + ["conducta = 'Observación'"])
            )
            cursor.execute(query_observacion, params)
            resultados_observacion = cursor.fetchall()
            tiempos_observacion = [r[0] for r in resultados_observacion if r[0] is not None and r[0] > 0]
            metricas_por_conducta['observacion'] = {
                'total': len(tiempos_observacion),
                'estadisticas': cls.calcular_estadisticas(tiempos_observacion)
            }
            
            # Calcular tiempos para pacientes hospitalizados
            query_hospitalizacion = query.replace(
                " AND ".join(condiciones),
                " AND ".join(condiciones + ["conducta = 'Hospitalización'"])
            )
            cursor.execute(query_hospitalizacion, params)
            resultados_hospitalizacion = cursor.fetchall()
            tiempos_hospitalizacion = [r[0] for r in resultados_hospitalizacion if r[0] is not None and r[0] > 0]
            metricas_por_conducta['hospitalizacion'] = {
                'total': len(tiempos_hospitalizacion),
                'estadisticas': cls.calcular_estadisticas(tiempos_hospitalizacion)
            }
            
            conn.close()
            return {
                'total_pacientes': len(tiempos),
                'estadisticas': estadisticas,
                'por_conducta': metricas_por_conducta
            }
            
        except Exception as e:
            print(f"Error al obtener métricas de tiempo total de atención: {str(e)}")
            return {
                'total_pacientes': 0,
                'estadisticas': {
                    'promedio': None,
                    'mediana': None,
                    'p90': None
                },
                'por_conducta': {
                    'alta': {'total': 0, 'estadisticas': {'promedio': None, 'mediana': None, 'p90': None}},
                    'observacion': {'total': 0, 'estadisticas': {'promedio': None, 'mediana': None, 'p90': None}},
                    'hospitalizacion': {'total': 0, 'estadisticas': {'promedio': None, 'mediana': None, 'p90': None}}
                }
            }
            
    @classmethod
    def obtener_todas_metricas(cls, area=None, fecha_inicio=None, fecha_fin=None, clase_triage=None):
        """
        Obtiene todas las métricas disponibles en un solo diccionario.
        
        Args:
            area (str, opcional): Área para filtrar los datos
            fecha_inicio (str, opcional): Fecha de inicio del rango
            fecha_fin (str, opcional): Fecha de fin del rango
            clase_triage (str, opcional): Clase de triage para filtrar (1-5)
            
        Returns:
            dict: Diccionario con todas las métricas recopiladas
        """
        # Recolectar todas las métricas individuales
        metricas_triage = cls.obtener_metricas_triage(area, fecha_inicio, fecha_fin, clase_triage)
        metricas_ci = cls.obtener_metricas_consulta_ingreso(area, fecha_inicio, fecha_fin, clase_triage)
        metricas_labs = cls.obtener_metricas_laboratorios(area, fecha_inicio, fecha_fin, clase_triage)
        metricas_ix = cls.obtener_metricas_imagenes(area, fecha_inicio, fecha_fin, clase_triage)
        metricas_ic = cls.obtener_metricas_interconsulta(area, fecha_inicio, fecha_fin, clase_triage)
        metricas_rv = cls.obtener_metricas_rv(area, fecha_inicio, fecha_fin, clase_triage)
        metricas_tiempo_total = cls.obtener_metricas_tiempo_total(area, fecha_inicio, fecha_fin, clase_triage)
        
        # Crear diccionario consolidado
        return {
            'triage': metricas_triage,
            'consulta_ingreso': metricas_ci,
            'laboratorios': metricas_labs,
            'imagenes': metricas_ix,
            'interconsulta': metricas_ic,
            'revaloracion': metricas_rv,
            'tiempo_total': metricas_tiempo_total,
            'configuracion': {
                'area': area or 'todas',
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'clase_triage': clase_triage
            }
        }

    @classmethod
    def generar_datos_linea_tiempo(cls, area=None, fecha_inicio=None, fecha_fin=None):
        """Genera los datos para el gráfico de línea temporal con agrupación inteligente"""
        try:
            start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d") if isinstance(fecha_inicio, str) else fecha_inicio
            end_date = datetime.strptime(fecha_fin, "%Y-%m-%d") if isinstance(fecha_fin, str) else fecha_fin
            
            days_difference = (end_date - start_date).days
            
            if days_difference <= 2:
                grouping = "hourly"
                format_str = "%H:%M"
                sql_format = "%H"
                group_by = "HOUR(ingreso)"
            elif days_difference > 2 and days_difference <= 31:  # Up to a month: show daily
                grouping = "daily"
                format_str = "%d %b"
                sql_format = "%Y-%m-%d"
                group_by = "DATE(ingreso)"
            elif days_difference > 31 and days_difference <= 92:  # Up to 3 months: show weekly
                grouping = "weekly"
                format_str = "Sem %U"
                sql_format = "%Y%U"
                group_by = "YEARWEEK(ingreso, 1)"
            elif days_difference > 92 and days_difference <= 365:  # Up to a year: show monthly
                grouping = "monthly"
                format_str = "%b %Y"
                sql_format = "%Y-%m"
                group_by = "DATE_FORMAT(ingreso, '%%Y-%%m')"
            else:  # More than a year: show quarterly
                grouping = "quarterly"
                format_str = "Q%q %Y"
                sql_format = "%Y-%q"
                group_by = "CONCAT(YEAR(ingreso), '-', QUARTER(ingreso))"
            
            # Create SQL query with dynamic grouping
            query = f"""
                    SELECT 
                        {group_by} AS date_group,
                        AVG(TIMESTAMPDIFF(MINUTE, ingreso, alta_timestamp)) AS avg_time
                    FROM 
                        pacientes
                    WHERE 
                        ingreso BETWEEN %s AND %s
                        AND alta_timestamp IS NOT NULL
                        {" AND ubicacion LIKE %s" if area else ""}
                    GROUP BY 
                        date_group
                    ORDER BY 
                        date_group
                """
                
            params = [fecha_inicio, fecha_fin]
            if area:
                params.append(f"%{area}%")
                
            # Execute query
            with cls.conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()
            
            # Depuración
            print(f"Resultados de la consulta: {results}")
            print(f"SQL usado: {query}")
            print(f"Parámetros: {params}")
            print(f"Agrupación: {grouping}")
                        
            # Process results based on grouping
            etiquetas = []
            datos = []

            for row in results:
                date_str = str(row[0])  # Asegurar que sea string
                avg_time = row[1]
                
                # Format date string based on grouping
                if grouping == "hourly":
                    # Handle hourly format - the date_str will be the hour (0-23)
                    try:
                        hour = int(date_str)
                        etiquetas.append(f"{hour:02d}:00")
                    except ValueError:
                        etiquetas.append(f"Hora {date_str}")
                elif grouping == "daily":
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    etiquetas.append(date_obj.strftime(format_str))
                elif grouping == "weekly":
                    # YEARWEEK devuelve formato YYYYWW sin guión, o puede ser entero
                    try:
                        # Si el resultado es como "202329" (año 2023, semana 29)
                        if len(date_str) >= 6:
                            year = date_str[:4]
                            week = date_str[4:6]
                            # Crear una fecha para la semana usando el primer día de la semana
                            date_obj = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
                            etiquetas.append(f"Sem {week}/{year}")
                        else:
                            # Formato alternativo o fallback
                            etiquetas.append(f"Sem {date_str}")
                    except ValueError as e:
                        print(f"Error procesando fecha semanal: {e}, valor: {date_str}")
                        etiquetas.append(f"Sem {date_str}")
                elif grouping == "monthly":
                    date_obj = datetime.strptime(date_str, "%Y-%m")
                    etiquetas.append(date_obj.strftime(format_str))
                elif grouping == "quarterly":
                    year, quarter = date_str.split('-')
                    etiquetas.append(f"Q{quarter} {year}")
                
                datos.append(round(avg_time) if avg_time else 0)
            
            if not results:
                print(f"No hay datos para el gráfico temporal: fecha_inicio={fecha_inicio}, fecha_fin={fecha_fin}, area={area}")
                return {
                    "etiquetas": [],
                    "datos": [],
                    "grouping": grouping  # Mantener grouping para consistencia
                }
                
            # Retornar datos correctos
            return {
                "etiquetas": etiquetas,
                "datos": datos,
                "grouping": grouping
            }
            
        except Exception as e:
            print(f"Error generando datos de línea temporal: {str(e)}")
            # Return empty data structure on error
            return {
                "etiquetas": [],
                "datos": [],
                "grouping": "daily"
            }
                            
    @classmethod
    def generar_datos_barras_comparativas(cls, area=None, fecha_inicio=None, fecha_fin=None, clase_triage=None):
        """
        Genera datos para el gráfico de barras de tiempos promedios por etapa.
        
        Args:
            area (str, opcional): Área para filtrar los datos
            fecha_inicio (str, opcional): Fecha de inicio del rango
            fecha_fin (str, opcional): Fecha de fin del rango
            clase_triage (str, opcional): Clase de triage para filtrar (1-5)
            
        Returns:
            dict: Diccionario con etiquetas y datos para el gráfico
        """
        try:
            # Obtener métricas de todas las etapas
            metricas = cls.obtener_todas_metricas(area, fecha_inicio, fecha_fin, clase_triage)
            
            # Extraer los datos relevantes para el gráfico
            etiquetas = ['Triage', 'Consulta de Ingreso', 'Laboratorios', 'Imágenes', 'Interconsulta', 'Revaloración']
            datos = [
                metricas['triage'].get('estadisticas', {}).get('promedio', 0) or 0,
                metricas['consulta_ingreso'].get('estadisticas', {}).get('promedio', 0) or 0,
                metricas['laboratorios'].get('estadisticas_total', {}).get('promedio', 0) or 0,
                metricas['imagenes'].get('estadisticas_total', {}).get('promedio', 0) or 0,
                metricas['interconsulta'].get('estadisticas_total', {}).get('promedio', 0) or 0,
                metricas['revaloracion'].get('estadisticas', {}).get('promedio', 0) or 0
            ]
            
            return {
                'etiquetas': etiquetas,
                'datos': datos
            }
            
        except Exception as e:
            print(f"Error al generar datos de barras comparativas: {str(e)}")
            return {
                'etiquetas': [],
                'datos': []
            }

    @classmethod
    def obtener_metricas_cumplimiento_sla(cls, area=None, fecha_inicio=None, fecha_fin=None, clase_triage=None):
        """
        Calcula las métricas de cumplimiento de SLA para cada etapa.
        
        Args:
            area (str, opcional): Área para filtrar los datos
            fecha_inicio (str, opcional): Fecha de inicio del rango
            fecha_fin (str, opcional): Fecha de fin del rango
            clase_triage (str, opcional): Clase de triage para filtrar (1-5)
            
        Returns:
            dict: Diccionario con porcentajes de cumplimiento para cada etapa
        """
        try:
            conn = cls.conectar()
            cursor = conn.cursor()
            
            # Definir SLAs objetivo (en minutos) para cada etapa y clase de triage
            slas = {
                # Formato: {clase_triage: tiempo_objetivo_en_minutos}
                'triage': {'1': 0, '2': 30, '3': 120, '4': 30, '5': 60},
                'ci': {'1': 210, '2': 210, '3': 360, '4': 420, '5': 420},
                'labs': {'1': 360, '2': 360, '3': 360, '4': 360, '5': 360},
                'ix': {'1': 360, '2': 360, '3': 360, '4': 360, '5': 360},
                'inter': {'1': 30, '2': 45, '3': 60, '4': 120, '5': 180},
                'rv': {'1': 30, '2': 60, '3': 120, '4': 240, '5': 360}
            }
            
            # Construir condiciones de filtro comunes
            condiciones_base = []
            params_base = []
            
            if area:
                condiciones_base.append("ubicacion LIKE %s")
                params_base.append(f"%{area}%")
            
            if clase_triage:
                condiciones_base.append("triage = %s")
                params_base.append(clase_triage)
            
            if fecha_inicio:
                condiciones_base.append("ingreso >= %s")
                params_base.append(fecha_inicio)
                
            if fecha_fin:
                condiciones_base.append("ingreso <= %s")
                params_base.append(fecha_fin)
            
            # Calcular cumplimiento para cada etapa
            resultados = {}
            
            # Triaje
            condiciones = condiciones_base.copy() + ["triage IN ('1', '2', '3', '4', '5') AND triage_timestamp IS NOT NULL"]
            params = params_base.copy()
            
            query = """
                SELECT 
                    triage,
                    TIMESTAMPDIFF(MINUTE, ingreso, triage_timestamp) as tiempo_triage
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones)
            
            cursor.execute(query, params)
            triage_data = cursor.fetchall()
            
            # Calcular cumplimiento
            total_triage = len(triage_data)
            if total_triage > 0:
                cumplidos_triage = sum(1 for t, tiempo in triage_data if tiempo <= slas['triage'].get(t, 30))
                resultados['triage'] = round((cumplidos_triage / total_triage) * 100)
            else:
                resultados['triage'] = 0
            
            # Consulta de Ingreso (CI)
            condiciones = condiciones_base.copy() + ["ci = 'Realizado' AND ci_no_realizado_timestamp IS NOT NULL AND ci_realizado_timestamp IS NOT NULL"]
            params = params_base.copy()
            
            query = """
                SELECT 
                    triage,
                    TIMESTAMPDIFF(MINUTE, ci_no_realizado_timestamp, ci_realizado_timestamp) as tiempo_ci
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones)
            
            cursor.execute(query, params)
            ci_data = cursor.fetchall()
            
            total_ci = len(ci_data)
            if total_ci > 0:
                cumplidos_ci = sum(1 for t, tiempo in ci_data if tiempo <= slas['ci'].get(t, 60))
                resultados['ci'] = round((cumplidos_ci / total_ci) * 100)
            else:
                resultados['ci'] = 0
            
            # Laboratorios
            condiciones = condiciones_base.copy() + ["labs = 'Resultados completos' AND labs_solicitados_timestamp IS NOT NULL AND labs_completos_timestamp IS NOT NULL"]
            params = params_base.copy()
            
            query = """
                SELECT 
                    triage,
                    TIMESTAMPDIFF(MINUTE, labs_solicitados_timestamp, labs_completos_timestamp) as tiempo_labs
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones)
            
            cursor.execute(query, params)
            labs_data = cursor.fetchall()
            
            total_labs = len(labs_data)
            if total_labs > 0:
                cumplidos_labs = sum(1 for t, tiempo in labs_data if tiempo <= slas['labs'].get(t, 90))
                resultados['labs'] = round((cumplidos_labs / total_labs) * 100)
            else:
                resultados['labs'] = 0
            
            # Imágenes (IX)
            condiciones = condiciones_base.copy() + ["ix = 'Resultados completos' AND ix_solicitados_timestamp IS NOT NULL AND ix_completos_timestamp IS NOT NULL"]
            params = params_base.copy()
            
            query = """
                SELECT 
                    triage,
                    TIMESTAMPDIFF(MINUTE, ix_solicitados_timestamp, ix_completos_timestamp) as tiempo_ix
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones)
            
            cursor.execute(query, params)
            ix_data = cursor.fetchall()
            
            total_ix = len(ix_data)
            if total_ix > 0:
                cumplidos_ix = sum(1 for t, tiempo in ix_data if tiempo <= slas['ix'].get(t, 90))
                resultados['ix'] = round((cumplidos_ix / total_ix) * 100)
            else:
                resultados['ix'] = 0
            
            # Interconsulta
            condiciones = condiciones_base.copy() + ["inter = 'Realizada' AND inter_abierta_timestamp IS NOT NULL AND inter_realizada_timestamp IS NOT NULL"]
            params = params_base.copy()
            
            query = """
                SELECT 
                    triage,
                    TIMESTAMPDIFF(MINUTE, inter_abierta_timestamp, inter_realizada_timestamp) as tiempo_inter
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones)
            
            cursor.execute(query, params)
            inter_data = cursor.fetchall()
            
            total_inter = len(inter_data)
            if total_inter > 0:
                cumplidos_inter = sum(1 for t, tiempo in inter_data if tiempo <= slas['inter'].get(t, 60))
                resultados['inter'] = round((cumplidos_inter / total_inter) * 100)
            else:
                resultados['inter'] = 0
            
            # Revaloración (RV)
            condiciones = condiciones_base.copy() + ["rv = 'Realizado' AND rv_no_realizado_timestamp IS NOT NULL AND rv_realizado_timestamp IS NOT NULL"]
            params = params_base.copy()
            
            query = """
                SELECT 
                    triage,
                    TIMESTAMPDIFF(MINUTE, rv_no_realizado_timestamp, rv_realizado_timestamp) as tiempo_rv
                FROM 
                    pacientes
                WHERE 
                    """ + " AND ".join(condiciones)
            
            cursor.execute(query, params)
            rv_data = cursor.fetchall()
            
            total_rv = len(rv_data)
            if total_rv > 0:
                cumplidos_rv = sum(1 for t, tiempo in rv_data if tiempo <= slas['rv'].get(t, 120))
                resultados['rv'] = round((cumplidos_rv / total_rv) * 100)
            else:
                resultados['rv'] = 0
            
            conn.close()
            return resultados
            
        except Exception as e:
            print(f"Error al calcular métricas de cumplimiento SLA: {str(e)}")
            return {
                'triage': 0,
                'ci': 0,
                'labs': 0,
                'ix': 0,
                'inter': 0,
                'rv': 0
            }
    
    @classmethod
    def obtener_metricas_paciente(cls, paciente_id):
        """
        Obtiene las métricas específicas para un paciente y las compara con su área
        para generar un reporte individual.
        """
        conn = None
        try:
            conn = cls.conectar()
            cursor = conn.cursor()
            
            # Primero obtenemos los datos básicos del paciente incluyendo su estado actual y tiempos
            cursor.execute("""
                SELECT p.nombre, p.documento, p.ubicacion, p.triage, p.ci, p.labs, p.ix, 
                    p.inter, p.rv, p.conducta, p.ingreso
                FROM pacientes p
                WHERE p.id = %s
            """, (paciente_id,))
            
            datos_paciente_basic = cursor.fetchone()
            
            if not datos_paciente_basic:
                print(f"No se encontró el paciente con ID {paciente_id}")
                return None
            
            nombre = datos_paciente_basic[0]
            documento = datos_paciente_basic[1]
            ubicacion = datos_paciente_basic[2]
            
            # Extraer el área (primera parte de la ubicación)
            area = ubicacion.split(' - ')[0] if ' - ' in ubicacion else ubicacion
            
            # Obtener fecha de ingreso para filtrar métricas comparativas en mismo período
            fecha_ingreso = datos_paciente_basic[10]
            # Crear rango de fechas: 30 días antes y después del ingreso
            from datetime import datetime, timedelta
            if isinstance(fecha_ingreso, str):
                fecha_ingreso = datetime.strptime(fecha_ingreso, "%Y-%m-%d %H:%M:%S")
            
            fecha_inicio = (fecha_ingreso - timedelta(days=30)).strftime("%Y-%m-%d")
            fecha_fin = (fecha_ingreso + timedelta(days=30)).strftime("%Y-%m-%d")
            
            # Obtener métricas del área para comparación usando el mismo rango de fechas
            metricas_area = {
                'triage': cls.obtener_metricas_triage(area=area, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin),
                'consulta_ingreso': cls.obtener_metricas_consulta_ingreso(area=area, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin),
                'laboratorios': cls.obtener_metricas_laboratorios(area=area, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin),
                'imagenes': cls.obtener_metricas_imagenes(area=area, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin),
                'interconsulta': cls.obtener_metricas_interconsulta(area=area, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin),
                'revaloracion': cls.obtener_metricas_rv(area=area, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin),
                'tiempo_total': cls.obtener_metricas_tiempo_total(area=area, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
            }
            
            # Obtener métricas del paciente desde la tabla metricas_pacientes
            cursor.execute("""
                SELECT * 
                FROM metricas_pacientes
                WHERE paciente_id = %s
            """, (paciente_id,))
            
            metricas = cursor.fetchone()
            
            if not metricas:
                print(f"No hay métricas disponibles para el paciente ID {paciente_id}")
                # Si no hay métricas, crear estructura vacía pero no retornar None
                metricas_dict = {}
            else:
                # Obtener las columnas para mapear índices
                cursor.execute("DESCRIBE metricas_pacientes")
                columnas = [col[0] for col in cursor.fetchall()]
                
                # Crear un diccionario con las métricas del paciente
                metricas_dict = {columnas[i]: metricas[i] for i in range(len(columnas))}
            
            # Crear un diccionario estructurado con las métricas para el reporte
            estadisticas = {
                "paciente": {
                    "id": paciente_id,
                    "nombre": nombre,
                    "documento": documento,
                    "ubicacion": ubicacion,
                    "area": area,
                    "estado_actual": {
                        "triage": datos_paciente_basic[3],
                        "ci": datos_paciente_basic[4],
                        "labs": datos_paciente_basic[5],
                        "ix": datos_paciente_basic[6],
                        "inter": datos_paciente_basic[7],
                        "rv": datos_paciente_basic[8],
                        "conducta": datos_paciente_basic[9]
                    },
                    "ingreso": str(fecha_ingreso)
                },
                "metricas": {
                    "triage": {
                        "tiempo": metricas_dict.get('tiempo_triage', 0),
                        "clase": metricas_dict.get('clase_triage', "")
                    },
                    "ci": {
                        "tiempo": metricas_dict.get('tiempo_ci', 0)
                    },
                    "labs": {
                        "tiempo": metricas_dict.get('tiempo_labs_total', 0),
                        "tiempo_solicitud": metricas_dict.get('tiempo_labs_solicitud', 0),
                        "tiempo_resultados": metricas_dict.get('tiempo_labs_resultados', 0)
                    },
                    "ix": {
                        "tiempo": metricas_dict.get('tiempo_ix_total', 0),
                        "tiempo_solicitud": metricas_dict.get('tiempo_ix_solicitud', 0),
                        "tiempo_resultados": metricas_dict.get('tiempo_ix_resultados', 0)
                    },
                    "inter": {
                        "tiempo": metricas_dict.get('tiempo_inter_total', 0),
                        "tiempo_apertura": metricas_dict.get('tiempo_inter_apertura', 0),
                        "tiempo_realizacion": metricas_dict.get('tiempo_inter_realizacion', 0)
                    },
                    "rv": {
                        "tiempo": metricas_dict.get('tiempo_rv', 0)
                    }
                },
                "tiempo_total": metricas_dict.get('tiempo_total_atencion', 0),
                "promedios_area": metricas_area,
                "area": area
            }
            
            if conn:
                conn.close()
            return estadisticas
            
        except Exception as e:
            print(f"Error al obtener métricas del paciente: {str(e)}")
            import traceback
            traceback.print_exc()
            if conn:
                conn.close()
            return None