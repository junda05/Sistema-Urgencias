import pymysql
import numpy as np
from datetime import datetime, timedelta
from Back_end.ModeloMetricas import ModeloMetricas
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate

class TestMetricas:
    """
    Clase para probar y verificar el cálculo de métricas
    desde la base de datos para la generación de reportes.
    """
    
    @staticmethod
    def formatear_tiempo(minutos):
        """
        Convierte minutos a formato hora:minutos
        """
        if minutos is None:
            return "--:--"
        
        horas = minutos // 60
        mins = minutos % 60
        return f"{horas}h {mins}m"
    
    @staticmethod
    def imprimir_titulo(texto):
        """Imprime un título formateado en la consola"""
        print("\n" + "="*80)
        print(f" {texto} ".center(80, "="))
        print("="*80 + "\n")
    
    @staticmethod
    def imprimir_estadisticas(titulo, estadisticas):
        """Muestra estadísticas formateadas en la consola"""
        print(f"\n{titulo}:")
        
        if not estadisticas or not estadisticas.get('estadisticas'):
            print("  No hay datos disponibles.")
            return
        
        datos = estadisticas['estadisticas']
        total = estadisticas.get('total_pacientes', 0)
        
        tabla = [
            ["Total de pacientes", total],
            ["Promedio", TestMetricas.formatear_tiempo(datos.get('promedio'))],
            ["Mediana", TestMetricas.formatear_tiempo(datos.get('mediana'))],
            ["Percentil 90", TestMetricas.formatear_tiempo(datos.get('p90'))]
        ]
        
        print(tabulate(tabla, headers=["Métrica", "Valor"], tablefmt="grid"))
    
    @classmethod
    def probar_metricas_globales(cls):
        """
        Prueba todas las métricas globales del sistema y muestra los resultados
        """
        cls.imprimir_titulo("PRUEBA DE MÉTRICAS GLOBALES")
        
        # Probar cada tipo de métrica
        metricas_triage = ModeloMetricas.obtener_metricas_triage()
        cls.imprimir_estadisticas("MÉTRICAS DE TRIAGE", metricas_triage)
        
        metricas_ci = ModeloMetricas.obtener_metricas_consulta_ingreso()
        cls.imprimir_estadisticas("MÉTRICAS DE CONSULTA DE INGRESO", metricas_ci)
            
        metricas_labs = ModeloMetricas.obtener_metricas_laboratorios()
        print("\nMÉTRICAS DE LABORATORIOS:")
        cls.imprimir_estadisticas("  EN ESPERA DE RESULTADOS", {
            'total_pacientes': metricas_labs.get('total_pacientes_solicitud', 0),
            'estadisticas': metricas_labs.get('estadisticas_solicitud')
        })
        cls.imprimir_estadisticas("  RESULTADOS", {
            'total_pacientes': metricas_labs.get('total_pacientes_resultados', 0),
            'estadisticas': metricas_labs.get('estadisticas_resultados')
        })
        cls.imprimir_estadisticas("  TOTAL", {
            'total_pacientes': metricas_labs.get('total_pacientes_total', 0),
            'estadisticas': metricas_labs.get('estadisticas_total')
        })
        
        # Corregido: Usar correctamente las métricas de imágenes
        metricas_ix = ModeloMetricas.obtener_metricas_imagenes()
        print("\nMÉTRICAS DE IMÁGENES DIAGNÓSTICAS:")
        cls.imprimir_estadisticas("  EN ESPERA DE RESULTADOS", {
            'total_pacientes': metricas_ix.get('total_pacientes_solicitud', 0),
            'estadisticas': metricas_ix.get('estadisticas_solicitud')
        })
        cls.imprimir_estadisticas("  RESULTADOS", {
            'total_pacientes': metricas_ix.get('total_pacientes_resultados', 0),
            'estadisticas': metricas_ix.get('estadisticas_resultados')
        })
        cls.imprimir_estadisticas("  TOTAL", {
            'total_pacientes': metricas_ix.get('total_pacientes_total', 0),
            'estadisticas': metricas_ix.get('estadisticas_total')
        })
        
        metricas_ic = ModeloMetricas.obtener_metricas_interconsulta()
        # Para interconsulta hay tres conjuntos de estadísticas
        if metricas_ic:
            print("\nMÉTRICAS DE INTERCONSULTA:")
            print("  Tiempo de apertura:")
            cls.imprimir_estadisticas("    Apertura", {
                'total_pacientes': metricas_ic.get('total_pacientes', 0),
                'estadisticas': metricas_ic.get('estadisticas_apertura')
            })
            cls.imprimir_estadisticas("    Realización", {
                'total_pacientes': metricas_ic.get('total_pacientes', 0),
                'estadisticas': metricas_ic.get('estadisticas_realizacion')
            })
            cls.imprimir_estadisticas("    Total", {
                'total_pacientes': metricas_ic.get('total_pacientes', 0),
                'estadisticas': metricas_ic.get('estadisticas_total')
            })
        
        metricas_rv = ModeloMetricas.obtener_metricas_rv()
        cls.imprimir_estadisticas("MÉTRICAS DE REVALORACIÓN", metricas_rv)
        
        metricas_total = ModeloMetricas.obtener_metricas_tiempo_total()
        cls.imprimir_estadisticas("MÉTRICAS DE TIEMPO TOTAL", metricas_total)
        
        # Si hay datos por conducta, mostrarlos
        if metricas_total and 'por_conducta' in metricas_total:
            print("\nTIEMPOS POR CONDUCTA:")
            conductas = metricas_total['por_conducta']
            
            for conducta, datos in conductas.items():
                cls.imprimir_estadisticas(f"  {conducta.upper()}", {
                    'total_pacientes': datos.get('total', 0),
                    'estadisticas': datos.get('estadisticas')
                })
    
    @classmethod
    def probar_metricas_por_area(cls, area):
        """
        Prueba las métricas para un área específica
        """
        cls.imprimir_titulo(f"PRUEBA DE MÉTRICAS PARA ÁREA: {area}")
        
        # Probar cada tipo de métrica filtrada por área
        metricas_triage = ModeloMetricas.obtener_metricas_triage(area=area)
        cls.imprimir_estadisticas("MÉTRICAS DE TRIAGE", metricas_triage)
        
        metricas_ci = ModeloMetricas.obtener_metricas_consulta_ingreso(area=area)
        cls.imprimir_estadisticas("MÉTRICAS DE CONSULTA DE INGRESO", metricas_ci)
        
        metricas_labs = ModeloMetricas.obtener_metricas_laboratorios(area=area)
        print("\nMÉTRICAS DE LABORATORIOS:")
        cls.imprimir_estadisticas("  EN ESPERA DE RESULTADOS", {
            'total_pacientes': metricas_labs.get('total_pacientes_solicitud', 0),
            'estadisticas': metricas_labs.get('estadisticas_solicitud')
        })
        cls.imprimir_estadisticas("  RESULTADOS", {
            'total_pacientes': metricas_labs.get('total_pacientes_resultados', 0),
            'estadisticas': metricas_labs.get('estadisticas_resultados')
        })
        cls.imprimir_estadisticas("  TOTAL", {
            'total_pacientes': metricas_labs.get('total_pacientes_total', 0),
            'estadisticas': metricas_labs.get('estadisticas_total')
        })
        
        # Corregido: Usar correctamente las métricas de imágenes para el área
        metricas_ix = ModeloMetricas.obtener_metricas_imagenes(area=area)
        print("\nMÉTRICAS DE IMÁGENES DIAGNÓSTICAS:")
        cls.imprimir_estadisticas("  EN ESPERA DE RESULTADOS", {
            'total_pacientes': metricas_ix.get('total_pacientes_solicitud', 0),
            'estadisticas': metricas_ix.get('estadisticas_solicitud')
        })
        cls.imprimir_estadisticas("  RESULTADOS", {
            'total_pacientes': metricas_ix.get('total_pacientes_resultados', 0),
            'estadisticas': metricas_ix.get('estadisticas_resultados')
        })
        cls.imprimir_estadisticas("  TOTAL", {
            'total_pacientes': metricas_ix.get('total_pacientes_total', 0),
            'estadisticas': metricas_ix.get('estadisticas_total')
        })
        
        metricas_ic = ModeloMetricas.obtener_metricas_interconsulta(area=area)
        # Para interconsulta hay tres conjuntos de estadísticas
        if metricas_ic:
            print("\nMÉTRICAS DE INTERCONSULTA:")
            print("  Tiempo de apertura:")
            cls.imprimir_estadisticas("    Apertura", {
                'total_pacientes': metricas_ic.get('total_pacientes', 0),
                'estadisticas': metricas_ic.get('estadisticas_apertura')
            })
            cls.imprimir_estadisticas("    Realización", {
                'total_pacientes': metricas_ic.get('total_pacientes', 0),
                'estadisticas': metricas_ic.get('estadisticas_realizacion')
            })
            cls.imprimir_estadisticas("    Total", {
                'total_pacientes': metricas_ic.get('total_pacientes', 0),
                'estadisticas': metricas_ic.get('estadisticas_total')
            })
        
        metricas_rv = ModeloMetricas.obtener_metricas_rv(area=area)
        cls.imprimir_estadisticas("MÉTRICAS DE REVALORACIÓN", metricas_rv)
        
        metricas_total = ModeloMetricas.obtener_metricas_tiempo_total(area=area)
        cls.imprimir_estadisticas("MÉTRICAS DE TIEMPO TOTAL", metricas_total)
        
        # Si hay datos por conducta, mostrarlos
        if metricas_total and 'por_conducta' in metricas_total:
            print("\nTIEMPOS POR CONDUCTA:")
            conductas = metricas_total['por_conducta']
            
            for conducta, datos in conductas.items():
                cls.imprimir_estadisticas(f"  {conducta.upper()}", {
                    'total_pacientes': datos.get('total', 0),
                    'estadisticas': datos.get('estadisticas')
                })
                
    @staticmethod
    def conectar_db():
        """Establece conexión a la base de datos usando credenciales directas"""
        try:
            return pymysql.connect(
                host="Mauricio",
                user="Urgencias_1",
                password="Josma@0409",
                database="sistema_visualizacion"
            )
        except Exception as e:
            print(f"Error de conexión a la base de datos: {str(e)}")
            return None
        
    @classmethod
    def probar_metricas_paciente(cls, paciente_id):
        """
        Obtiene y muestra las métricas específicas para un paciente
        """
        cls.imprimir_titulo(f"MÉTRICAS PARA PACIENTE ID: {paciente_id}")
        
        # Conectar a la base de datos
        conn = cls.conectar_db()
        if not conn:
            print("No se pudo conectar a la base de datos.")
            return
        
        try:
            cursor = conn.cursor()
            
            # Primero obtenemos los datos básicos del paciente
            cursor.execute("""
                SELECT nombre, documento, ubicacion 
                FROM pacientes
                WHERE id = %s
            """, (paciente_id,))
            
            datos_paciente = cursor.fetchone()
            
            if not datos_paciente:
                print(f"No se encontró el paciente con ID {paciente_id}")
                return
            
            nombre = datos_paciente[0]
            documento = datos_paciente[1]
            ubicacion = datos_paciente[2]
            
            # Extraer las métricas
            area = ubicacion.split(' - ')[0] if ' - ' in ubicacion else ubicacion
            
            print(f"Nombre: {nombre}")
            print(f"Documento: {documento}")
            print(f"Ubicación: {ubicacion}")
            print(f"Área: {area}\n")
            
            # Obtener métricas del área para comparación ANTES de intentar usarlas
            print("Obteniendo métricas del área...")
            area_triage = ModeloMetricas.obtener_metricas_triage(area=area)
            area_ci = ModeloMetricas.obtener_metricas_consulta_ingreso(area=area)
            area_labs = ModeloMetricas.obtener_metricas_laboratorios(area=area)
            area_ix = ModeloMetricas.obtener_metricas_imagenes(area=area)
            area_ic = ModeloMetricas.obtener_metricas_interconsulta(area=area)
            area_rv = ModeloMetricas.obtener_metricas_rv(area=area)
            area_total = ModeloMetricas.obtener_metricas_tiempo_total(area=area)
            
            # Ahora obtenemos las métricas del paciente (si existen)
            cursor.execute("""
                SELECT * 
                FROM metricas_pacientes
                WHERE paciente_id = %s
            """, (paciente_id,))
            
            metricas = cursor.fetchone()
            
            if not metricas:
                print("No hay métricas disponibles para este paciente.")
                return
                
            # Obtener las columnas para mapear índices
            cursor.execute("DESCRIBE metricas_pacientes")
            columnas = [col[0] for col in cursor.fetchall()]
            
            # Crear un diccionario para acceder a los valores por nombre de columna
            metricas_dict = {columnas[i]: metricas[i] for i in range(len(columnas))}
            
            # Mostrar métricas del paciente
            print("\nMétricas del paciente:")
            metricas_paciente = []
            
            # Triage
            if 'tiempo_triage' in metricas_dict:
                tiempo_triage = metricas_dict.get('tiempo_triage')
                clase_triage = metricas_dict.get('clase_triage', '--')
                metricas_paciente.append(["Triage (clase " + str(clase_triage) + ")", cls.formatear_tiempo(tiempo_triage)])
            
            # Consulta de Ingreso
            if 'tiempo_ci' in metricas_dict:
                metricas_paciente.append(["Consulta de Ingreso", cls.formatear_tiempo(metricas_dict.get('tiempo_ci'))])
            
            # Laboratorios
            if 'tiempo_labs_solicitud' in metricas_dict:
                metricas_paciente.append(["Laboratorios (EN ESPERA DE RESULTADOS)", cls.formatear_tiempo(metricas_dict.get('tiempo_labs_solicitud'))])
            
            if 'tiempo_labs_resultados' in metricas_dict:
                metricas_paciente.append(["Laboratorios (resultados)", cls.formatear_tiempo(metricas_dict.get('tiempo_labs_resultados'))])
            
            if 'tiempo_labs_total' in metricas_dict:
                metricas_paciente.append(["Laboratorios (total)", cls.formatear_tiempo(metricas_dict.get('tiempo_labs_total'))])
                
            # Imágenes diagnósticas
            if 'tiempo_ix_solicitud' in metricas_dict:
                metricas_paciente.append(["Imágenes (EN ESPERA DE RESULTADOS)", cls.formatear_tiempo(metricas_dict.get('tiempo_ix_solicitud'))])
            
            if 'tiempo_ix_resultados' in metricas_dict:
                metricas_paciente.append(["Imágenes (resultados)", cls.formatear_tiempo(metricas_dict.get('tiempo_ix_resultados'))])
            
            if 'tiempo_ix_total' in metricas_dict:
                metricas_paciente.append(["Imágenes (total)", cls.formatear_tiempo(metricas_dict.get('tiempo_ix_total'))])
            
            # Interconsulta
            if 'tiempo_inter_apertura' in metricas_dict and metricas_dict.get('tiempo_inter_apertura') is not None:
                metricas_paciente.append(["Interconsulta (apertura)", cls.formatear_tiempo(metricas_dict.get('tiempo_inter_apertura'))])
            
            if 'tiempo_inter_realizacion' in metricas_dict and metricas_dict.get('tiempo_inter_realizacion') is not None:
                metricas_paciente.append(["Interconsulta (realización)", cls.formatear_tiempo(metricas_dict.get('tiempo_inter_realizacion'))])
            
            if 'tiempo_inter_total' in metricas_dict and metricas_dict.get('tiempo_inter_total') is not None:
                metricas_paciente.append(["Interconsulta (total)", cls.formatear_tiempo(metricas_dict.get('tiempo_inter_total'))])
            
            # Revaloración
            if 'tiempo_rv' in metricas_dict and metricas_dict.get('tiempo_rv') is not None:
                metricas_paciente.append(["Revaloración", cls.formatear_tiempo(metricas_dict.get('tiempo_rv'))])
            
            # Tiempo total
            if 'tiempo_total_atencion' in metricas_dict and metricas_dict.get('tiempo_total_atencion') is not None:
                metricas_paciente.append(["Tiempo total de atención", cls.formatear_tiempo(metricas_dict.get('tiempo_total_atencion'))])
            
            if metricas_paciente:
                print(tabulate(metricas_paciente, headers=["Proceso", "Tiempo"], tablefmt="grid"))
            else:
                print("No se encontraron métricas para mostrar.")
            
            # Ahora creamos las comparaciones
            print("\nComparación con métricas del área:")
            
            comparacion = []
            
            # Triage
            if 'tiempo_triage' in metricas_dict and area_triage and 'estadisticas' in area_triage and area_triage['estadisticas'].get('promedio'):
                tiempo_triage = metricas_dict.get('tiempo_triage')
                if tiempo_triage is not None:
                    diff_triage = tiempo_triage - area_triage['estadisticas']['promedio']
                    comparacion.append([
                        "Triage", 
                        cls.formatear_tiempo(tiempo_triage), 
                        cls.formatear_tiempo(area_triage['estadisticas']['promedio']), 
                        f"{abs(diff_triage):.1f} min {'menos' if diff_triage < 0 else 'más'}"
                    ])
            
            # Consulta de Ingreso
            if 'tiempo_ci' in metricas_dict and area_ci and 'estadisticas' in area_ci and area_ci['estadisticas'].get('promedio'):
                tiempo_ci = metricas_dict.get('tiempo_ci')
                if tiempo_ci is not None:
                    diff_ci = tiempo_ci - area_ci['estadisticas']['promedio']
                    comparacion.append([
                        "Consulta de Ingreso", 
                        cls.formatear_tiempo(tiempo_ci), 
                        cls.formatear_tiempo(area_ci['estadisticas']['promedio']), 
                        f"{abs(diff_ci):.1f} min {'menos' if diff_ci < 0 else 'más'}"
                    ])
            
            # Labs - ahora comparamos los diferentes tiempos
            if 'tiempo_labs_solicitud' in metricas_dict and area_labs and 'estadisticas_solicitud' in area_labs and area_labs['estadisticas_solicitud'].get('promedio'):
                tiempo_labs_solicitud = metricas_dict.get('tiempo_labs_solicitud')
                if tiempo_labs_solicitud is not None:
                    diff_labs = tiempo_labs_solicitud - area_labs['estadisticas_solicitud']['promedio']
                    comparacion.append([
                        "Labs (EN ESPERA DE RESULTADOS)", 
                        cls.formatear_tiempo(tiempo_labs_solicitud), 
                        cls.formatear_tiempo(area_labs['estadisticas_solicitud']['promedio']), 
                        f"{abs(diff_labs):.1f} min {'menos' if diff_labs < 0 else 'más'}"
                    ])

            if 'tiempo_labs_resultados' in metricas_dict and area_labs and 'estadisticas_resultados' in area_labs and area_labs['estadisticas_resultados'].get('promedio'):
                tiempo_labs_resultados = metricas_dict.get('tiempo_labs_resultados')
                if tiempo_labs_resultados is not None:
                    diff_labs = tiempo_labs_resultados - area_labs['estadisticas_resultados']['promedio']
                    comparacion.append([
                        "Labs (resultados)", 
                        cls.formatear_tiempo(tiempo_labs_resultados), 
                        cls.formatear_tiempo(area_labs['estadisticas_resultados']['promedio']), 
                        f"{abs(diff_labs):.1f} min {'menos' if diff_labs < 0 else 'más'}"
                    ])

            if 'tiempo_labs_total' in metricas_dict and area_labs and 'estadisticas_total' in area_labs and area_labs['estadisticas_total'].get('promedio'):
                tiempo_labs_total = metricas_dict.get('tiempo_labs_total')
                if tiempo_labs_total is not None:
                    diff_labs = tiempo_labs_total - area_labs['estadisticas_total']['promedio']
                    comparacion.append([
                        "Labs (total)", 
                        cls.formatear_tiempo(tiempo_labs_total), 
                        cls.formatear_tiempo(area_labs['estadisticas_total']['promedio']), 
                        f"{abs(diff_labs):.1f} min {'menos' if diff_labs < 0 else 'más'}"
                    ])
                
            # IX - comparamos los diferentes tiempos
            if 'tiempo_ix_solicitud' in metricas_dict and area_ix and 'estadisticas_solicitud' in area_ix and area_ix['estadisticas_solicitud'].get('promedio'):
                tiempo_ix_solicitud = metricas_dict.get('tiempo_ix_solicitud')
                if tiempo_ix_solicitud is not None:
                    diff_ix = tiempo_ix_solicitud - area_ix['estadisticas_solicitud']['promedio']
                    comparacion.append([
                        "Imágenes (EN ESPERA DE RESULTADOS)", 
                        cls.formatear_tiempo(tiempo_ix_solicitud), 
                        cls.formatear_tiempo(area_ix['estadisticas_solicitud']['promedio']), 
                        f"{abs(diff_ix):.1f} min {'menos' if diff_ix < 0 else 'más'}"
                    ])

            if 'tiempo_ix_resultados' in metricas_dict and area_ix and 'estadisticas_resultados' in area_ix and area_ix['estadisticas_resultados'].get('promedio'):
                tiempo_ix_resultados = metricas_dict.get('tiempo_ix_resultados')
                if tiempo_ix_resultados is not None:
                    diff_ix = tiempo_ix_resultados - area_ix['estadisticas_resultados']['promedio']
                    comparacion.append([
                        "Imágenes (resultados)", 
                        cls.formatear_tiempo(tiempo_ix_resultados), 
                        cls.formatear_tiempo(area_ix['estadisticas_resultados']['promedio']), 
                        f"{abs(diff_ix):.1f} min {'menos' if diff_ix < 0 else 'más'}"
                    ])

            if 'tiempo_ix_total' in metricas_dict and area_ix and 'estadisticas_total' in area_ix and area_ix['estadisticas_total'].get('promedio'):
                tiempo_ix_total = metricas_dict.get('tiempo_ix_total')
                if tiempo_ix_total is not None:
                    diff_ix = tiempo_ix_total - area_ix['estadisticas_total']['promedio']
                    comparacion.append([
                        "Imágenes (total)", 
                        cls.formatear_tiempo(tiempo_ix_total), 
                        cls.formatear_tiempo(area_ix['estadisticas_total']['promedio']), 
                        f"{abs(diff_ix):.1f} min {'menos' if diff_ix < 0 else 'más'}"
                    ])
            
            # Interconsulta (total) - comparación
            if 'tiempo_inter_total' in metricas_dict and area_ic and 'estadisticas_total' in area_ic and area_ic['estadisticas_total'].get('promedio'):
                tiempo_inter = metricas_dict.get('tiempo_inter_total')
                if tiempo_inter is not None:
                    diff_inter = tiempo_inter - area_ic['estadisticas_total']['promedio']
                    comparacion.append([
                        "Interconsulta", 
                        cls.formatear_tiempo(tiempo_inter), 
                        cls.formatear_tiempo(area_ic['estadisticas_total']['promedio']), 
                        f"{abs(diff_inter):.1f} min {'menos' if diff_inter < 0 else 'más'}"
                    ])
            
            # Revaloración - comparación
            if 'tiempo_rv' in metricas_dict and area_rv and 'estadisticas' in area_rv and area_rv['estadisticas'].get('promedio'):
                tiempo_rv = metricas_dict.get('tiempo_rv')
                if tiempo_rv is not None:
                    diff_rv = tiempo_rv - area_rv['estadisticas']['promedio']
                    comparacion.append([
                        "Revaloración", 
                        cls.formatear_tiempo(tiempo_rv), 
                        cls.formatear_tiempo(area_rv['estadisticas']['promedio']), 
                        f"{abs(diff_rv):.1f} min {'menos' if diff_rv < 0 else 'más'}"
                    ])
            
            # Tiempo total de atención - comparación
            if 'tiempo_total_atencion' in metricas_dict and area_total and 'estadisticas' in area_total and area_total['estadisticas'].get('promedio'):
                tiempo_total = metricas_dict.get('tiempo_total_atencion')
                if tiempo_total is not None:
                    diff_total = tiempo_total - area_total['estadisticas']['promedio']
                    comparacion.append([
                        "Tiempo total", 
                        cls.formatear_tiempo(tiempo_total), 
                        cls.formatear_tiempo(area_total['estadisticas']['promedio']), 
                        f"{abs(diff_total):.1f} min {'menos' if diff_total < 0 else 'más'}"
                    ])
            
            if comparacion:
                print(tabulate(comparacion, headers=["Proceso", "Paciente", "Promedio área", "Diferencia"], tablefmt="grid"))
            else:
                print("No hay datos suficientes para realizar comparaciones.")
            
        except Exception as e:
            print(f"Error al obtener métricas del paciente: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                conn.close()
    
# Función para ejecutar pruebas desde la línea de comandos
if __name__ == "__main__":
    import sys
    
    print("Sistema de prueba de métricas para reportes")
    print("-----------------------------------------")
    print("Opciones disponibles:")
    print("1. Probar métricas globales")
    print("2. Probar métricas por área")
    print("3. Probar métricas para un paciente específico")
    
    opcion = input("\nSeleccione una opción (1-3): ")
    
    if opcion == "1":
        TestMetricas.probar_metricas_globales()
    elif opcion == "2":
        areas = ["Amarilla", "Antigua", "Clini", "Pasillos", "Pediatría", "Sala de espera"]
        print("\nÁreas disponibles:")
        for i, area in enumerate(areas, 1):
            print(f"{i}. {area}")
        
        seleccion = input("\nSeleccione un área (1-6): ")
        try:
            indice = int(seleccion) - 1
            if 0 <= indice < len(areas):
                TestMetricas.probar_metricas_por_area(areas[indice])
            else:
                print("Selección inválida.")
        except ValueError:
            print("Por favor ingrese un número.")
    elif opcion == "3":
        paciente_id = input("\nIngrese ID del paciente: ")
        try:
            paciente_id = int(paciente_id)
            TestMetricas.probar_metricas_paciente(paciente_id)
        except ValueError:
            print("Por favor ingrese un ID válido.")
    else:
        print("Opción inválida.")