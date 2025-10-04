import os
import pymysql
import configparser
from Back_end.Manejo_DB import ModeloConfiguracion

class ModeloUsuarios:
    # Definir constantes para los tipos de privilegios
    PRIVILEGIOS = {
        'solo_lectura': [
            'SELECT', 
            'SHOW VIEW'
        ],
        'crud': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'SHOW VIEW'],
        'admin': ['ALL PRIVILEGES']
    }
    PRIVILEGIOS_GLOBALES_ADMIN = ['CREATE USER', 'GRANT OPTION', 'RELOAD']
    PRIVILEGIOS_MYSQL_DB = ['SELECT']
    
    @staticmethod
    def get_admin_credentials():
        """
        Obtener credenciales del administrador actual o de configuración
        - Si el usuario actual es administrador, usa sus credenciales
        - Si no, intenta leer de configuración o usa valores por defecto
        """
        # Intentar obtener credenciales del usuario autenticado
        from Back_end.Manejo_DB import ModeloAutenticacion
        credenciales = ModeloAutenticacion.obtener_credenciales()
        
        # Verificar si el usuario actual es administrador y tiene credenciales completas
        if (credenciales.get('usuario') and credenciales.get('contrasena') and 
            ModeloUsuarios.obtener_rol_usuario(credenciales.get('usuario')) == 'admin'):
            return {
                'user': credenciales.get('usuario'),
                'password': credenciales.get('contrasena')
            }
        
        # Si el usuario no es admin o no hay credenciales, usar configuración
        config_path = ModeloConfiguracion.get_config_path()
        config = configparser.ConfigParser()
        
        if os.path.exists(config_path):
            config.read(config_path)
            if 'ADMIN' in config:
                return {
                    'user': config.get('ADMIN', 'user', fallback='Urgencias_1'),
                    'password': config.get('ADMIN', 'password', fallback='Josma@0409')
                }
        
        # Valores por defecto si no existe configuración
        return {'user': 'Urgencias_1', 'password': 'Josma@0409'}

    @staticmethod
    def crear_usuario(username, password, nombre_completo, host='%', es_admin=False):
        """
        Crea un nuevo usuario con los privilegios correspondientes según su tipo
        
        Args:
            username: Nombre de usuario a crear
            password: Contraseña para el usuario
            nombre_completo: Nombre completo del usuario
            host: Host desde el que se permitirá conectar (por defecto cualquiera)
            es_admin: Si es True, se crea un usuario con privilegios de administrador
            
        Returns:
            tuple: (éxito, mensaje)
        """
        if not ModeloUsuarios.validar_nombre_usuario(username):
            return False, "Nombre de usuario inválido"
            
        if not ModeloUsuarios.validar_password(password):
            return False, "Contraseña inválida"
            
        admin_credentials = ModeloUsuarios.get_admin_credentials()
        host_config = ModeloConfiguracion.cargar_configuracion()
        
        try:
            # Conexión con credenciales de administrador
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password']
            )
            cursor = conn.cursor()
            
            # Verificar si el usuario ya existe
            cursor.execute("SELECT User FROM mysql.user WHERE User = %s", (username,))
            usuario_existe = cursor.fetchone() is not None
            
            # Asignar permisos según el tipo de usuario
            if es_admin:
                # Usuario administrador: todos los privilegios en el esquema
                tipo_usuario = "administrador"
                privilegios = ModeloUsuarios.PRIVILEGIOS['admin']
            else:
                # Usuario estándar: privilegios de lectura y específicos para preferencias
                tipo_usuario = "visualización"
                privilegios = ModeloUsuarios.PRIVILEGIOS['solo_lectura']
            
            # Si el usuario existe, actualizar sus privilegios
            if usuario_existe:
                if es_admin:
                    cursor.execute(f"""
                        GRANT {', '.join(privilegios)} ON sistema_visualizacion.* TO '{username}'@'{host}'
                        WITH GRANT OPTION
                    """)
                    
                    # Añadir permisos globales para administradores (separar los comandos)
                    cursor.execute(f"""
                        GRANT {', '.join(ModeloUsuarios.PRIVILEGIOS_GLOBALES_ADMIN)} ON *.* TO '{username}'@'{host}'
                    """)
                    
                    # Permisos específicos para la base de datos mysql
                    cursor.execute(f"""
                        GRANT {', '.join(ModeloUsuarios.PRIVILEGIOS_MYSQL_DB)} ON mysql.* TO '{username}'@'{host}'
                    """)
                else:
                    cursor.execute(f"""
                        GRANT {', '.join(privilegios)} ON sistema_visualizacion.* TO '{username}'@'{host}'
                    """)
            else:
                # Crear usuario con password
                cursor.execute(f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}'")
                
                # Otorgar privilegios
                if es_admin:
                    cursor.execute(f"""
                        GRANT {', '.join(privilegios)} ON sistema_visualizacion.* TO '{username}'@'{host}'
                        WITH GRANT OPTION
                    """)
                else:
                    cursor.execute(f"""
                        GRANT {', '.join(privilegios)} ON sistema_visualizacion.* TO '{username}'@'{host}'
                    """)
                    cursor.execute(f"""
                        GRANT SELECT ON mysql.user TO '{username}'@'{host}'
                    """)
            
            cursor.execute("FLUSH PRIVILEGES")
            conn.commit()
            
            # Guardar nombre completo en la tabla usuarios
            try:
                conn_app = pymysql.connect(
                    host=host_config,
                    user=admin_credentials['user'],
                    password=admin_credentials['password'],
                    database='sistema_visualizacion'
                )
                cursor_app = conn_app.cursor()
                
                # Actualizar tabla usuarios con el nombre completo y rol adecuado
                rol_admin = 1 if es_admin else 0
                rol_visitante = 0 if es_admin else 1
                
                cursor_app.execute("""
                    INSERT INTO usuarios (username, nombre_completo, rol_admin, rol_medico, rol_visitante) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        nombre_completo = VALUES(nombre_completo),
                        rol_admin = VALUES(rol_admin),
                        rol_medico = VALUES(rol_medico),
                        rol_visitante = VALUES(rol_visitante)
                """, (username, nombre_completo, rol_admin, 0, rol_visitante))
                
                conn_app.commit()
                conn_app.close()
            except Exception as e:
                print(f"Error al actualizar tabla usuarios: {str(e)}")
            
            accion = "actualizado" if usuario_existe else "creado"
            return True, f"Usuario {username} {accion} exitosamente con privilegios de {tipo_usuario}"
            
        except pymysql.Error as e:
            return False, f"Error al crear usuario: {str(e)}"
        finally:
            if 'conn' in locals() and conn:
                conn.close()
            
    @staticmethod
    def crear_usuario_crud(username, password, nombre_completo, host='%'):
        """
        Crea un nuevo usuario con privilegios CRUD (pero no administrativos)
        
        Args:
            username: Nombre de usuario a crear
            password: Contraseña para el usuario
            nombre_completo: Nombre completo del usuario
            host: Host desde el que se permitirá conectar
            
        Returns:
            tuple: (éxito, mensaje)
        """
        if not ModeloUsuarios.validar_nombre_usuario(username):
            return False, "El nombre de usuario no cumple con los requisitos"
            
        if not ModeloUsuarios.validar_password(password):
            return False, "La contraseña no cumple con los requisitos de seguridad"
            
        admin_credentials = ModeloUsuarios.get_admin_credentials()
        host_config = ModeloConfiguracion.cargar_configuracion()
        
        try:
            # Conexión con credenciales de administrador
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password']
            )
            cursor = conn.cursor()
            
            # Verificar si el usuario ya existe
            cursor.execute("SELECT User FROM mysql.user WHERE User = %s", (username,))
            if cursor.fetchone():
                # Si el usuario existe, modificar sus privilegios
                privilegios = ModeloUsuarios.PRIVILEGIOS['crud']
                cursor.execute(f"""
                    GRANT {', '.join(privilegios)}
                    ON sistema_visualizacion.* TO '{username}'@'{host}'
                """)
            else:
                # Crear usuario con password
                cursor.execute(f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}'")
                
                # Otorgar privilegios CRUD
                privilegios = ModeloUsuarios.PRIVILEGIOS['crud']
                cursor.execute(f"""
                    GRANT {', '.join(privilegios)}
                    ON sistema_visualizacion.* TO '{username}'@'{host}'
                """)
            
            cursor.execute("FLUSH PRIVILEGES")
            conn.commit()
            
            # Guardar nombre completo en la tabla usuarios
            try:
                conn_app = pymysql.connect(
                    host=host_config,
                    user=admin_credentials['user'],
                    password=admin_credentials['password'],
                    database='sistema_visualizacion'
                )
                cursor_app = conn_app.cursor()
                
                # Actualizar tabla usuarios con el nombre completo y rol médico
                cursor_app.execute("""
                    INSERT INTO usuarios (username, nombre_completo, rol_admin, rol_medico, rol_visitante) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        nombre_completo = VALUES(nombre_completo),
                        rol_admin = VALUES(rol_admin),
                        rol_medico = VALUES(rol_medico),
                        rol_visitante = VALUES(rol_visitante)
                """, (username, nombre_completo, 0, 1, 0))
                
                conn_app.commit()
                conn_app.close()
            except Exception as e:
                print(f"Error al actualizar tabla usuarios: {str(e)}")
            
            return True, f"Usuario {username} configurado exitosamente con privilegios CRUD"
            
        except pymysql.Error as e:
            return False, f"Error al crear/modificar usuario: {str(e)}"
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def actualizar_privilegios_usuario(username, tipo_privilegios, host='%'):
        """
        Actualiza los privilegios de un usuario existente
        
        Args:
            username: Nombre del usuario a actualizar
            tipo_privilegios: Tipo de privilegios ('solo_lectura', 'crud', 'admin')
            host: Host desde el que se permitirá conectar
            
        Returns:
            tuple: (éxito, mensaje)
        """
        if tipo_privilegios not in ModeloUsuarios.PRIVILEGIOS:
            return False, f"Tipo de privilegios '{tipo_privilegios}' no válido"
            
        admin_credentials = ModeloUsuarios.get_admin_credentials()
        host_config = ModeloConfiguracion.cargar_configuracion()
        
        try:
            # Conexión con credenciales de administrador
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password']
            )
            cursor = conn.cursor()
            
            # Verificar si el usuario existe
            cursor.execute("SELECT User FROM mysql.user WHERE User = %s", (username,))
            if not cursor.fetchone():
                return False, f"El usuario {username} no existe"
            
            # Revocar privilegios existentes (primero los normales, luego GRANT OPTION por separado)
            cursor.execute(f"REVOKE ALL PRIVILEGES ON sistema_visualizacion.* FROM '{username}'@'{host}'")
            try:
                # Revocar permisos globales
                cursor.execute(f"REVOKE {', '.join(ModeloUsuarios.PRIVILEGIOS_GLOBALES_ADMIN)} ON *.* FROM '{username}'@'{host}'")
            except pymysql.Error:
                # Ignorar errores si no tenía estos permisos
                pass
            
            try:
                # Revocar permisos de la base de datos mysql
                cursor.execute(f"REVOKE {', '.join(ModeloUsuarios.PRIVILEGIOS_MYSQL_DB)} ON mysql.* FROM '{username}'@'{host}'")
            except pymysql.Error:
                # Ignorar errores si no tenía estos permisos
                pass
                
            # Asignar nuevos privilegios
            if tipo_privilegios == 'admin':
                cursor.execute(f"""
                    GRANT {', '.join(ModeloUsuarios.PRIVILEGIOS['admin'])} ON sistema_visualizacion.* TO '{username}'@'{host}'
                    WITH GRANT OPTION
                """)
                
                # Añadir permisos globales para administradores (separados)
                cursor.execute(f"""
                    GRANT {', '.join(ModeloUsuarios.PRIVILEGIOS_GLOBALES_ADMIN)} ON *.* TO '{username}'@'{host}'
                """)
                
                # Permisos específicos para la base de datos mysql
                cursor.execute(f"""
                    GRANT {', '.join(ModeloUsuarios.PRIVILEGIOS_MYSQL_DB)} ON mysql.* TO '{username}'@'{host}'
                """)
            else:
                if tipo_privilegios == 'solo_lectura':
                    # Otorgar privilegios básicos de lectura (ÚNICAMENTE SELECT, SHOW VIEW)
                    cursor.execute(f"""
                        GRANT {', '.join(ModeloUsuarios.PRIVILEGIOS['solo_lectura'])} ON sistema_visualizacion.* TO '{username}'@'{host}'
                    """)
                else:
                    # Para CRUD y otros roles
                    privilegios = ModeloUsuarios.PRIVILEGIOS[tipo_privilegios]
                    cursor.execute(f"""
                        GRANT {', '.join(privilegios)} ON sistema_visualizacion.* TO '{username}'@'{host}'
                    """)
            
            cursor.execute("FLUSH PRIVILEGES")
            conn.commit()
            
            return True, f"Privilegios del usuario {username} actualizados a {tipo_privilegios}"
            
        except pymysql.Error as e:
            return False, f"Error al actualizar privilegios: {str(e)}"
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def crear_usuario_admin(username, password, nombre_completo, host='%'):
        """
        Crea un nuevo usuario con privilegios de administrador
        
        Args:
            username: Nombre de usuario a crear
            password: Contraseña para el usuario
            nombre_completo: Nombre completo del usuario
            host: Host desde el que se permitirá conectar
            
        Returns:
            tuple: (éxito, mensaje)
        """
        return ModeloUsuarios.crear_usuario(username, password, nombre_completo, host, es_admin=True)

    @staticmethod
    def inactivar_usuario(username):
        """
        Inactiva un usuario en el sistema y lo elimina de MySQL
        
        Args:
            username: Nombre de usuario a inactivar
            
        Returns:
            tuple: (éxito, mensaje)
        """
        admin_credentials = ModeloUsuarios.get_admin_credentials()
        host_config = ModeloConfiguracion.cargar_configuracion()
        
        try:
            # Conexión para actualizar el estado en la tabla usuarios
            conn_app = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password'],
                database='sistema_visualizacion'
            )
            cursor_app = conn_app.cursor()
            
            # Verificar si el usuario existe y está activo
            cursor_app.execute("""
                SELECT estado FROM usuarios WHERE username = %s
            """, (username,))
            
            result = cursor_app.fetchone()
            if not result:
                conn_app.close()
                return False, f"El usuario {username} no existe en la base de datos"
                
            if result[0] == 'inactivo':
                conn_app.close()
                return False, f"El usuario {username} ya está inactivo"
            
            # Actualizar estado a inactivo en la tabla usuarios
            cursor_app.execute("""
                UPDATE usuarios SET estado = 'inactivo' WHERE username = %s
            """, (username,))
            
            conn_app.commit()
            conn_app.close()
            
            # Ahora eliminar el usuario de MySQL
            conn_mysql = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password']
            )
            cursor_mysql = conn_mysql.cursor()
            
            # Eliminar el usuario de MySQL
            try:
                cursor_mysql.execute(f"DROP USER '{username}'@'%'")
                cursor_mysql.execute("FLUSH PRIVILEGES")
            except pymysql.Error as e:
                print(f"Error al eliminar usuario de MySQL: {str(e)}")
                
            conn_mysql.commit()
            conn_mysql.close()
            
            return True, f"Usuario {username} inactivado correctamente y eliminado de la base de datos"
        
        except Exception as e:
            return False, f"Error al inactivar usuario: {str(e)}"

    @staticmethod
    def cambiar_password(username, new_password):
        """
        Cambia la contraseña de un usuario existente
        
        Args:
            username: Nombre de usuario cuya contraseña se cambiará
            new_password: Nueva contraseña
            
        Returns:
            tuple: (éxito, mensaje)
        """
        if not ModeloUsuarios.validar_password(new_password):
            return False, "La contraseña no cumple con los requisitos de seguridad"
            
        admin_credentials = ModeloUsuarios.get_admin_credentials()
        host_config = ModeloConfiguracion.cargar_configuracion()
        
        try:
            # Conexión con credenciales de administrador
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password']
            )
            cursor = conn.cursor()
            
            # Verificar si el usuario existe
            cursor.execute("SELECT User FROM mysql.user WHERE User = %s", (username,))
            if not cursor.fetchone():
                conn.close()
                return False, f"El usuario {username} no existe"
            
            # Cambiar contraseña
            cursor.execute(f"ALTER USER '{username}'@'%' IDENTIFIED BY '{new_password}'")
            cursor.execute("FLUSH PRIVILEGES")
            
            conn.commit()
            conn.close()
            
            return True, f"Contraseña del usuario {username} cambiada exitosamente"
            
        except pymysql.Error as e:
            return False, f"Error al cambiar contraseña: {str(e)}"

    @staticmethod
    def validar_nombre_usuario(username):
        """
        Valida que el nombre de usuario cumpla con los requisitos:
        - Entre 4 y 16 caracteres
        - Solo letras, números y guiones bajos
        - No empieza con número
        
        Returns:
            bool: True si es válido, False si no
        """
        if not username or len(username) < 4 or len (username) > 16:
            return False
        
        if not username[0].isalpha():
            return False
            
        return all(c.isalnum() or c == '_' for c in username)
    
    @staticmethod
    def validar_password(password):
        """
        Valida que la contraseña cumpla con los requisitos mínimos:
        - Al menos 8 caracteres
        - Al menos una letra mayúscula
        - Al menos una letra minúscula
        - Al menos un número
        - Al menos un carácter especial
        
        Returns:
            bool: True si es válida, False si no
        """
        if not password or len(password) < 8:
            return False
            
        if not any(c.isupper() for c in password):
            return False
            
        if not any(c.islower() for c in password):
            return False
            
        if not any(c.isdigit() for c in password):
            return False
            
        if not any(not c.isalnum() for c in password):
            return False
            
        return True

    @staticmethod
    def verificar_usuario_existe(username):
        """
        Verifica si un nombre de usuario ya existe en la base de datos
        
        Args:
            username: Nombre de usuario a verificar
            
        Returns:
            bool: True si el usuario existe, False si no
        """
        if not username:
            return False
            
        admin_credentials = ModeloUsuarios.get_admin_credentials()
        host_config = ModeloConfiguracion.cargar_configuracion()
        
        try:
            # Primero intentamos verificar en la tabla de usuarios
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password'],
                database='sistema_visualizacion'
            )
            cursor = conn.cursor()
            
            # Verificar si el usuario existe en la tabla de usuarios
            cursor.execute("SELECT 1 FROM usuarios WHERE username = %s", (username,))
            exists = cursor.fetchone() is not None
            conn.close()
            
            if exists:
                return True
                
            try:
                # Crear una conexión usando el usuario root o administrador
                conn = pymysql.connect(
                    host=host_config,
                    user=admin_credentials['user'],
                    password=admin_credentials['password']
                )
                cursor = conn.cursor()
                
                # Verificar usuarios
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.user_privileges 
                    WHERE grantee LIKE %s
                """, (f"'%{username}%'",))
                
                count = cursor.fetchone()[0]
                conn.close()
                return count > 0
                
            except Exception as inner_e:
                print(f"Error secundario al verificar usuario: {str(inner_e)}")
                # Si ambos métodos fallan, asumimos que el usuario no existe
                return False
            
        except Exception as e:
            print(f"Error primario al verificar usuario: {str(e)}")
            return False

    @staticmethod
    def obtener_lista_usuarios():
        """
        Obtiene una lista de todos los usuarios de la base de datos con sus roles asignados
        desde la tabla 'usuarios'
        
        Returns:
            list: Lista de tuplas (id, nombre_usuario, estado, rol) donde:
                - id: identificador numérico del usuario
                - nombre_usuario: nombre del usuario
                - estado: 'activo' o 'inactivo'
                - rol: 'admin', 'medico', 'visitante' o None
        """
        admin_credentials = ModeloUsuarios.get_admin_credentials()
        host_config = ModeloConfiguracion.cargar_configuracion()
        
        try:
            # Conexión con credenciales de administrador
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password'],
                database='sistema_visualizacion'
            )
            cursor = conn.cursor()
            
            # Obtener lista de todos los usuarios en la tabla
            cursor.execute("""
                SELECT id, username, rol_admin, rol_medico, rol_visitante, estado, nombre_completo 
                FROM usuarios
                ORDER BY id
            """)
            
            usuarios_locales = {row[1]: row for row in cursor.fetchall()}
            
            # Obtener todos los usuarios MySQL activos
            cursor.execute(""" 
                SELECT User, Host FROM mysql.user 
                WHERE User NOT IN ('root', 'mysql.sys', 'mysql.session', 'mysql.infoschema')
                AND User != ''
                ORDER BY User
            """)
            
            mysql_users = {user[0]: user for user in cursor.fetchall()}
            
            usuarios = []
            id_temp = 10000  # ID temporal para usuarios con error
            
            # Primero procesar usuarios MySQL activos
            for username in mysql_users.keys():
                if username in usuarios_locales:
                    # Usuario existe en ambos lugares - está activo
                    user_data = usuarios_locales[username]
                    user_id = user_data[0]  # Usar el ID real de la base de datos
                    rol_admin, rol_medico, rol_visitante = user_data[2], user_data[3], user_data[4]
                    estado = 'activo'
                    nombre_completo = user_data[6] or f"Usuario {username}"
                    
                    # Si el estado era inactivo, actualizar a activo
                    if user_data[5] != 'activo':
                        cursor.execute("""
                            UPDATE usuarios SET estado = 'activo'
                            WHERE username = %s
                        """, (username,))
                        conn.commit()
                    
                    # Determinar rol principal
                    if rol_admin:
                        rol = 'admin'
                    elif rol_medico:
                        rol = 'medico'
                    elif rol_visitante:
                        rol = 'visitante'
                    else:
                        rol = None
                else:
                    # Usuario existe en MySQL pero no en la tabla - crear entrada
                    es_admin = ModeloUsuarios.verificar_rol_admin(username)
                    es_medico = ModeloUsuarios.verificar_rol_medico(username)
                    
                    # Determinar el rol principal
                    if es_admin:
                        rol = 'admin'
                        rol_admin, rol_medico, rol_visitante = 1, 0, 0
                    elif es_medico:
                        rol = 'medico'
                        rol_admin, rol_medico, rol_visitante = 0, 1, 0
                    else:
                        rol = 'visitante'
                        rol_admin, rol_medico, rol_visitante = 0, 0, 1
                    
                    # Crear entrada en tabla usuarios
                    try:
                        cursor.execute("""
                            INSERT INTO usuarios (username, nombre_completo, rol_admin, rol_medico, rol_visitante, estado)
                            VALUES (%s, %s, %s, %s, %s, 'activo')
                        """, (username, f"Usuario {username}", rol_admin, rol_medico, rol_visitante))
                        conn.commit()
                        
                        # Obtener el ID asignado en la base de datos
                        cursor.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
                        user_id = cursor.fetchone()[0]
                        
                        estado = 'activo'
                        nombre_completo = f"Usuario {username}"
                    except Exception as e:
                        print(f"Error al insertar usuario en tabla usuarios: {str(e)}")
                        # Usar un ID temporal si hay error
                        user_id = id_temp
                        id_temp += 1
                        continue
                
                # Agregar a la lista de usuarios usando el ID real de la base de datos
                usuarios.append((user_id, username, estado, rol))
            
            # Ahora procesar usuarios en la tabla que ya no existen en MySQL
            for username, user_data in usuarios_locales.items():
                if username not in mysql_users:
                    # Usuario existe en la tabla pero no en MySQL - marcar como inactivo
                    if user_data[5] == 'activo':
                        cursor.execute("""
                            UPDATE usuarios SET estado = 'inactivo'
                            WHERE username = %s
                        """, (username,))
                        conn.commit()
                    
                    # Usar el ID real de la base de datos
                    user_id = user_data[0]
                    
                    # Determinar rol principal
                    rol_admin, rol_medico, rol_visitante = user_data[2], user_data[3], user_data[4]
                    if rol_admin:
                        rol = 'admin'
                    elif rol_medico:
                        rol = 'medico'
                    elif rol_visitante:
                        rol = 'visitante'
                    else:
                        rol = None
                    
                    # Agregar a la lista de usuarios con estado inactivo
                    usuarios.append((user_id, username, 'inactivo', rol))
            
            conn.close()
            return usuarios
            
        except Exception as e:
            print(f"Error al obtener lista de usuarios: {str(e)}")
            return []

    @staticmethod
    def actualizar_roles_en_tabla(username, rol):
        """
        Actualiza los roles en la tabla usuarios para mantener consistencia
        
        Args:
            username: Nombre de usuario a actualizar
            rol: Rol asignado ('admin', 'medico', 'visitante')
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        try:
            admin_credentials = ModeloUsuarios.get_admin_credentials()
            host_config = ModeloConfiguracion.cargar_configuracion()
            
            # Valores por defecto para roles
            admin_val = 0
            medico_val = 0
            visitante_val = 0
            
            # Establecer valores según el rol asignado
            if rol == 'admin':
                admin_val = 1
            elif rol == 'crud':
                medico_val = 1
            elif rol == 'solo_lectura':
                visitante_val = 1
            
            # Conexión con credenciales de administrador
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password'],
                database='sistema_visualizacion'
            )
            cursor = conn.cursor()
            
            # Verificar si el usuario existe en la tabla
            cursor.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
            user_exists = cursor.fetchone() is not None
            
            if user_exists:
                # Actualizar roles del usuario existente
                cursor.execute("""
                    UPDATE usuarios 
                    SET rol_admin = %s, rol_medico = %s, rol_visitante = %s
                    WHERE username = %s
                """, (admin_val, medico_val, visitante_val, username))
            else:
                # Insertar nuevo usuario con roles
                cursor.execute("""
                    INSERT INTO usuarios (username, nombre_completo, rol_admin, rol_medico, rol_visitante, estado)
                    VALUES (%s, %s, %s, %s, %s, 'activo')
                """, (username, f"Usuario {username}", admin_val, medico_val, visitante_val))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error al actualizar roles en tabla usuarios: {str(e)}")
            return False

    @staticmethod
    def verificar_rol_admin(username):
        """
        Verifica si un usuario tiene rol de administrador
        consultando directamente la tabla usuarios
        
        Args:
            username: Nombre del usuario a verificar
            
        Returns:
            bool: True si tiene rol de administrador, False en caso contrario
        """
        return ModeloUsuarios.obtener_rol_usuario(username) == 'admin'
        
    @staticmethod
    def verificar_rol_medico(username):
        """
        Verifica si un usuario tiene rol de médico
        consultando directamente la tabla usuarios
        
        Args:
            username: Nombre del usuario a verificar
            
        Returns:
            bool: True si tiene rol de médico, False en caso contrario
        """
        return ModeloUsuarios.obtener_rol_usuario(username) == 'medico'
                 
    @staticmethod
    def conectar_db():
        """Establece conexión con la base de datos"""
        try:
            host_config = ModeloConfiguracion.cargar_configuracion()
            
            # Usar las credenciales del usuario actual autenticado desde ModeloAutenticacion
            from Back_end.Manejo_DB import ModeloAutenticacion
            credenciales = ModeloAutenticacion.obtener_credenciales()
            
            # Si no hay credenciales disponibles, usar admin_credentials como fallback
            if not credenciales.get('usuario') or not credenciales.get('contrasena'):
                admin_credentials = ModeloUsuarios.get_admin_credentials()
                conn = pymysql.connect(
                    host=host_config,
                    user=admin_credentials['user'],
                    password=admin_credentials['password'],
                    database='sistema_visualizacion'
                )
            else:
                # Usar las credenciales del usuario autenticado
                conn = pymysql.connect(
                    host=host_config,
                    user=credenciales['usuario'],
                    password=credenciales['contrasena'],
                    database='sistema_visualizacion'
                )
            return conn
        except Exception as e:
            print(f"Error de conexión: {str(e)}")
            return None
            
    @staticmethod
    def obtener_rol_usuario(username):
        """
        Obtiene el rol de un usuario directamente de la tabla usuarios.
        
        Args:
            username: Nombre de usuario
        
        Returns:
            str: El rol del usuario ('admin', 'medico', 'visitante') o 'visitante' por defecto
        """
        if not username:
            return 'visitante'  # Default role if no username provided
            
        try:
            # Conexión a la BD
            conn = ModeloUsuarios.conectar_db()
            if not conn:
                return 'visitante'  # Default role if connection fails
                
            cursor = conn.cursor()
            
            # Consultar los valores de los roles del usuario
            cursor.execute("""
                SELECT rol_admin, rol_medico, rol_visitante 
                FROM usuarios 
                WHERE username = %s
            """, (username,))
            
            resultado = cursor.fetchone()
            conn.close()
            
            # Si el usuario existe en la tabla, determinar su rol principal
            if resultado:
                rol_admin, rol_medico, rol_visitante = resultado
                
                if rol_admin:
                    return 'admin'
                elif rol_medico:
                    return 'medico'
                elif rol_visitante:
                    return 'visitante'
                else:
                    return 'visitante'  # Default to visitante if no role is set
                    
            # Si no está en la tabla usuarios, intentar detectar privilegios y crearlo
            # Este es un caso de recuperación para usuarios antiguos
            try:
                # Crear entrada por defecto con rol visitante para este usuario
                ModeloUsuarios.actualizar_roles_en_tabla(username, 'solo_lectura')
                return 'visitante'
            except:
                return 'visitante'  # Si falla la creación, asignar visitante por defecto
                
        except Exception as e:
            print(f"Error al obtener rol de usuario: {str(e)}")
            return 'visitante'