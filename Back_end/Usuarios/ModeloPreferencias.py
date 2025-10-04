import json
import os
import sys

class ModeloPreferencias:
    """
    Modelo para manejar las preferencias de usuario, incluyendo filtros de área
    y otras configuraciones personalizadas utilizando archivos JSON.
    """
    
    # Variable de clase para almacenar preferencias en memoria durante la sesión
    _cache_preferencias = {}
    
    @staticmethod
    def obtener_ruta_preferencias():
        """Obtiene la ruta donde se guardarán las preferencias como archivo"""
        if getattr(sys, 'frozen', False):
            ruta_base = os.path.dirname(sys.executable)
        else:
            ruta_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Crear carpeta 'preferencias' si no existe
        ruta_preferencias = os.path.join(ruta_base, 'preferencias')
        if not os.path.exists(ruta_preferencias):
            try:
                os.makedirs(ruta_preferencias)
            except Exception as e:
                print(f"No se pudo crear directorio de preferencias: {str(e)}")
                import tempfile
                ruta_preferencias = tempfile.gettempdir()
        
        return ruta_preferencias
    
    @staticmethod
    def guardar_preferencias_filtros(nombre_usuario, areas_filtradas):
        """
        Guarda las preferencias de filtros de área para un usuario en archivo JSON.
        
        Args:
            nombre_usuario: Usuario al que pertenecen las preferencias
            areas_filtradas: Lista de áreas seleccionadas
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        if not nombre_usuario:
            return False
        
        # Guardar en caché de memoria para la sesión actual
        if nombre_usuario not in ModeloPreferencias._cache_preferencias:
            ModeloPreferencias._cache_preferencias[nombre_usuario] = {}
        
        ModeloPreferencias._cache_preferencias[nombre_usuario]['filtros_area'] = areas_filtradas
        
        # Guardar en archivo JSON
        try:
            # Obtener ruta del archivo
            ruta_preferencias = ModeloPreferencias.obtener_ruta_preferencias()
            archivo_preferencias = os.path.join(ruta_preferencias, f"{nombre_usuario}_prefs.json")
            
            # Crear o cargar el contenido actual
            preferencias = {}
            if os.path.exists(archivo_preferencias):
                try:
                    with open(archivo_preferencias, 'r') as f:
                        preferencias = json.load(f)
                except:
                    preferencias = {}
            
            # Actualizar filtros
            preferencias['filtros_area'] = areas_filtradas
            
            # Guardar a archivo
            with open(archivo_preferencias, 'w') as f:
                json.dump(preferencias, f)
            
            print(f"Preferencias guardadas en archivo: {archivo_preferencias}")
            return True
        except Exception as e:
            print(f"Error al guardar preferencias en archivo: {str(e)}")
            return False
    
    @staticmethod
    def obtener_filtros_area(nombre_usuario, areas_disponibles):
        """
        Obtiene las preferencias de filtros de área para un usuario.
        Intenta primero desde la memoria caché, luego desde archivo.
        
        Args:
            nombre_usuario: Usuario del que se obtendrán las preferencias
            areas_disponibles: Lista de áreas disponibles por defecto
            
        Returns:
            list: Lista de áreas filtradas según las preferencias del usuario
        """
        if not nombre_usuario:
            return areas_disponibles
        
        # Verificar primero en la caché de memoria (para la sesión actual)
        if (nombre_usuario in ModeloPreferencias._cache_preferencias and 
            'filtros_area' in ModeloPreferencias._cache_preferencias[nombre_usuario]):
            filtros_cache = ModeloPreferencias._cache_preferencias[nombre_usuario]['filtros_area']
            # Validar áreas de caché
            filtros_validos = [area for area in filtros_cache if area in areas_disponibles]
            if filtros_validos:
                print(f"Usando filtros de caché para {nombre_usuario}")
                return filtros_validos
        
        # Intentar obtener desde archivo
        try:
            ruta_preferencias = ModeloPreferencias.obtener_ruta_preferencias()
            archivo_preferencias = os.path.join(ruta_preferencias, f"{nombre_usuario}_prefs.json")
            
            if os.path.exists(archivo_preferencias):
                try:
                    with open(archivo_preferencias, 'r') as f:
                        preferencias = json.load(f)
                    
                    if 'filtros_area' in preferencias and preferencias['filtros_area']:
                        # Validar que las áreas existan
                        filtros_validos = [area for area in preferencias['filtros_area'] 
                                          if area in areas_disponibles]
                        
                        if filtros_validos:
                            # Actualizar caché
                            if nombre_usuario not in ModeloPreferencias._cache_preferencias:
                                ModeloPreferencias._cache_preferencias[nombre_usuario] = {}
                            ModeloPreferencias._cache_preferencias[nombre_usuario]['filtros_area'] = filtros_validos
                            
                            print(f"Usando filtros de archivo para {nombre_usuario}")
                            return filtros_validos
                except Exception as e:
                    print(f"Error al cargar preferencias desde archivo: {str(e)}")
        except Exception as e:
            print(f"Error accediendo al archivo de preferencias: {str(e)}")
        
        # Si no se encuentran preferencias, devolver todas las áreas
        print(f"No se encontraron filtros guardados para {nombre_usuario}, usando áreas por defecto")
        return areas_disponibles
    
    @staticmethod
    def guardar_tiempo_paginacion(nombre_usuario, tiempo_segundos):
        """
        Guarda la preferencia de tiempo de paginación para un usuario.
        
        Args:
            nombre_usuario: Usuario al que pertenece la preferencia
            tiempo_segundos: Tiempo en segundos entre cambios de página
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        if not nombre_usuario:
            return False
            
        # Guardar en caché de memoria para la sesión actual
        if nombre_usuario not in ModeloPreferencias._cache_preferencias:
            ModeloPreferencias._cache_preferencias[nombre_usuario] = {}
            
        ModeloPreferencias._cache_preferencias[nombre_usuario]['tiempo_paginacion'] = tiempo_segundos
        
        # Guardar en archivo JSON
        try:
            ruta_preferencias = ModeloPreferencias.obtener_ruta_preferencias()
            archivo_preferencias = os.path.join(ruta_preferencias, f"{nombre_usuario}_prefs.json")
            
            # Crear o cargar contenido actual
            preferencias = {}
            if os.path.exists(archivo_preferencias):
                try:
                    with open(archivo_preferencias, 'r') as f:
                        preferencias = json.load(f)
                except:
                    preferencias = {}
            
            # Actualizar tiempo de paginación
            preferencias['tiempo_paginacion'] = tiempo_segundos
            
            # Guardar a archivo
            with open(archivo_preferencias, 'w') as f:
                json.dump(preferencias, f)
                
            print(f"Tiempo de paginación guardado en archivo: {archivo_preferencias}")
            return True
        except Exception as e:
            print(f"Error al guardar tiempo de paginación: {str(e)}")
            return False
            
    @staticmethod
    def obtener_tiempo_paginacion(nombre_usuario, valor_predeterminado=5):
        """
        Obtiene la preferencia de tiempo de paginación para un usuario.
        
        Args:
            nombre_usuario: Usuario del que se obtendrán las preferencias
            valor_predeterminado: Valor a devolver si no hay preferencia guardada
            
        Returns:
            int: Tiempo en segundos entre cambios de página
        """
        if not nombre_usuario:
            return valor_predeterminado
            
        # Verificar primero en la caché de memoria
        if (nombre_usuario in ModeloPreferencias._cache_preferencias and
            'tiempo_paginacion' in ModeloPreferencias._cache_preferencias[nombre_usuario]):
            return ModeloPreferencias._cache_preferencias[nombre_usuario]['tiempo_paginacion']
            
        # Intentar obtener desde archivo
        try:
            ruta_preferencias = ModeloPreferencias.obtener_ruta_preferencias()
            archivo_preferencias = os.path.join(ruta_preferencias, f"{nombre_usuario}_prefs.json")
            
            if os.path.exists(archivo_preferencias):
                try:
                    with open(archivo_preferencias, 'r') as f:
                        preferencias = json.load(f)
                        
                    if 'tiempo_paginacion' in preferencias:
                        tiempo = preferencias['tiempo_paginacion']
                        
                        # Actualizar caché
                        if nombre_usuario not in ModeloPreferencias._cache_preferencias:
                            ModeloPreferencias._cache_preferencias[nombre_usuario] = {}
                        ModeloPreferencias._cache_preferencias[nombre_usuario]['tiempo_paginacion'] = tiempo
                        
                        print(f"Usando tiempo de paginación desde archivo: {tiempo}s")
                        return tiempo
                except Exception as e:
                    print(f"Error al cargar tiempo de paginación: {str(e)}")
        except Exception as e:
            print(f"Error accediendo al archivo de preferencias: {str(e)}")
            
        # Si no se encuentra preferencia, devolver valor predeterminado
        print(f"No se encontró tiempo de paginación para {nombre_usuario}, usando valor predeterminado: {valor_predeterminado}s")
        return valor_predeterminado
