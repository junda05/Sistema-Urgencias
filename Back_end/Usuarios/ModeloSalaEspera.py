from Back_end.Manejo_DB import ModeloPaciente

class ModeloSalaEspera(ModeloPaciente):
    """Modelo específico para la sala de espera con funcionalidades limitadas"""
    
    def obtener_datos_pacientes(self):
        """Obtiene datos de pacientes para la vista de sala de espera"""
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre, documento, triage, ci, labs, ix, inter, rv, pendientes, 
                ubicacion, ingreso, triage_timestamp, id, observacion_timestamp 
            FROM pacientes 
            ORDER BY ingreso DESC
        """)
        datos = cursor.fetchall()
        conn.close()
        return datos
    
    def obtener_datos_pacientes_filtrados(self, areas_seleccionadas=None):
        """Obtiene datos de pacientes filtrados por áreas específicas"""
        conn = self.conectar()
        cursor = conn.cursor()
        
        if areas_seleccionadas and len(areas_seleccionadas) > 0:
            # Crear una lista de condiciones para cada área seleccionada
            condiciones = []
            for area in areas_seleccionadas:
                condiciones.append(f"ubicacion LIKE '{area}%'")
            
            # Unir las condiciones con OR
            condicion_where = " OR ".join(condiciones)
            
            # Consulta con filtro de áreas
            query = f"""
                SELECT nombre, documento, triage, ci, labs, ix, inter, rv, pendientes, 
                    ubicacion, ingreso, triage_timestamp, id, observacion_timestamp 
                FROM pacientes 
                WHERE {condicion_where}
                ORDER BY ingreso DESC
            """
        else:
            # Si no hay áreas seleccionadas o la lista está vacía, traer todos los datos
            query = """
                SELECT nombre, documento, triage, ci, labs, ix, inter, rv, pendientes, 
                    ubicacion, ingreso, triage_timestamp, id, observacion_timestamp 
                FROM pacientes 
                ORDER BY ingreso DESC
            """
        
        cursor.execute(query)
        datos = cursor.fetchall()
        conn.close()
        return datos