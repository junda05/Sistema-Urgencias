import os
import pymysql
import configparser
from backend.database import ConfigurationModel

class UsersModel:
    # Define the constants for the privilege types
    PRIVILEGES = {
        'read_only': [
            'SELECT',
            'SHOW VIEW'
        ],
        'crud': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'SHOW VIEW'],
        'admin': ['ALL PRIVILEGES']
    }
    ADMIN_GLOBAL_PRIVILEGES = ['CREATE USER', 'GRANT OPTION', 'RELOAD']
    MYSQL_DB_PRIVILEGES = ['SELECT']

    @staticmethod
    def get_admin_credentials():
        """
        Get the credentials of the current administrator or from the configuration
        - If the current user is an administrator, use their credentials
        - Otherwise, try to read from the configuration or use the default values
        """
        # Try to get the credentials of the authenticated user
        from backend.database import AuthenticationModel
        credentials = AuthenticationModel.get_credentials()

        # Check whether the current user is an administrator and has complete credentials
        if (credentials.get('user') and credentials.get('password') and
            UsersModel.get_user_role(credentials.get('user')) == 'admin'):
            return {
                'user': credentials.get('user'),
                'password': credentials.get('password')
            }

        # If the user is not an admin or there are no credentials, use the configuration
        config_path = ConfigurationModel.get_config_path()
        config = configparser.ConfigParser()

        if os.path.exists(config_path):
            config.read(config_path)
            if 'ADMIN' in config:
                return {
                    'user': config.get('ADMIN', 'user', fallback='emergency_admin'),
                    'password': config.get('ADMIN', 'password', fallback='CHANGE_ME_BEFORE_DEPLOYMENT')
                }

        # Default values if there is no configuration
        return {'user': 'emergency_admin', 'password': 'CHANGE_ME_BEFORE_DEPLOYMENT'}

    @staticmethod
    def create_user(username, password, full_name, host='%', is_admin=False):
        """
        Creates a new user with the privileges matching their type

        Args:
            username: Username to create
            password: Password for the user
            full_name: Full name of the user
            host: Host the user will be allowed to connect from (any by default)
            is_admin: If True, a user with administrator privileges is created

        Returns:
            tuple: (success, message)
        """
        if not UsersModel.validate_username(username):
            return False, "Invalid username"

        if not UsersModel.validate_password(password):
            return False, "Invalid password"

        admin_credentials = UsersModel.get_admin_credentials()
        host_config = ConfigurationModel.load_configuration()

        try:
            # Connection using the administrator credentials
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password'],
                charset='utf8mb4'
            )
            cursor = conn.cursor()

            # Check whether the user already exists
            cursor.execute("SELECT User FROM mysql.user WHERE User = %s", (username,))
            user_exists = cursor.fetchone() is not None

            # Assign the permissions according to the user type
            if is_admin:
                # Administrator user: every privilege on the schema
                user_type = "administrator"
                privileges = UsersModel.PRIVILEGES['admin']
            else:
                # Standard user: read privileges and specific ones for preferences
                user_type = "visualization"
                privileges = UsersModel.PRIVILEGES['read_only']

            # If the user exists, update their privileges
            if user_exists:
                if is_admin:
                    cursor.execute(f"""
                        GRANT {', '.join(privileges)} ON urgentix.* TO '{username}'@'{host}'
                        WITH GRANT OPTION
                    """)

                    # Add the global permissions for administrators (separate the commands)
                    cursor.execute(f"""
                        GRANT {', '.join(UsersModel.ADMIN_GLOBAL_PRIVILEGES)} ON *.* TO '{username}'@'{host}'
                    """)

                    # Specific permissions for the mysql database
                    cursor.execute(f"""
                        GRANT {', '.join(UsersModel.MYSQL_DB_PRIVILEGES)} ON mysql.* TO '{username}'@'{host}'
                    """)
                else:
                    cursor.execute(f"""
                        GRANT {', '.join(privileges)} ON urgentix.* TO '{username}'@'{host}'
                    """)
            else:
                # Create the user with a password
                cursor.execute(f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}'")

                # Grant the privileges
                if is_admin:
                    cursor.execute(f"""
                        GRANT {', '.join(privileges)} ON urgentix.* TO '{username}'@'{host}'
                        WITH GRANT OPTION
                    """)
                else:
                    cursor.execute(f"""
                        GRANT {', '.join(privileges)} ON urgentix.* TO '{username}'@'{host}'
                    """)
                    cursor.execute(f"""
                        GRANT SELECT ON mysql.user TO '{username}'@'{host}'
                    """)

            cursor.execute("FLUSH PRIVILEGES")
            conn.commit()

            # Save the full name in the users table
            try:
                conn_app = pymysql.connect(
                    host=host_config,
                    user=admin_credentials['user'],
                    password=admin_credentials['password'],
                    database='urgentix',
                    charset='utf8mb4'
                )
                cursor_app = conn_app.cursor()

                # Update the users table with the full name and the appropriate role
                role_admin = 1 if is_admin else 0
                role_visitor = 0 if is_admin else 1

                cursor_app.execute("""
                    INSERT INTO users (username, full_name, role_admin, role_doctor, role_visitor)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        full_name = VALUES(full_name),
                        role_admin = VALUES(role_admin),
                        role_doctor = VALUES(role_doctor),
                        role_visitor = VALUES(role_visitor)
                """, (username, full_name, role_admin, 0, role_visitor))

                conn_app.commit()
                conn_app.close()
            except Exception as e:
                print(f"Error updating the users table: {str(e)}")

            action = "updated" if user_exists else "created"
            return True, f"User {username} {action} successfully with {user_type} privileges"

        except pymysql.Error as e:
            return False, f"Error creating the user: {str(e)}"
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def create_crud_user(username, password, full_name, host='%'):
        """
        Creates a new user with CRUD (but not administrative) privileges

        Args:
            username: Username to create
            password: Password for the user
            full_name: Full name of the user
            host: Host the user will be allowed to connect from

        Returns:
            tuple: (success, message)
        """
        if not UsersModel.validate_username(username):
            return False, "The username does not meet the requirements"

        if not UsersModel.validate_password(password):
            return False, "The password does not meet the security requirements"

        admin_credentials = UsersModel.get_admin_credentials()
        host_config = ConfigurationModel.load_configuration()

        try:
            # Connection using the administrator credentials
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password'],
                charset='utf8mb4'
            )
            cursor = conn.cursor()

            # Check whether the user already exists
            cursor.execute("SELECT User FROM mysql.user WHERE User = %s", (username,))
            if cursor.fetchone():
                # If the user exists, modify their privileges
                privileges = UsersModel.PRIVILEGES['crud']
                cursor.execute(f"""
                    GRANT {', '.join(privileges)}
                    ON urgentix.* TO '{username}'@'{host}'
                """)
            else:
                # Create the user with a password
                cursor.execute(f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}'")

                # Grant the CRUD privileges
                privileges = UsersModel.PRIVILEGES['crud']
                cursor.execute(f"""
                    GRANT {', '.join(privileges)}
                    ON urgentix.* TO '{username}'@'{host}'
                """)

            cursor.execute("FLUSH PRIVILEGES")
            conn.commit()

            # Save the full name in the users table
            try:
                conn_app = pymysql.connect(
                    host=host_config,
                    user=admin_credentials['user'],
                    password=admin_credentials['password'],
                    database='urgentix',
                    charset='utf8mb4'
                )
                cursor_app = conn_app.cursor()

                # Update the users table with the full name and the doctor role
                cursor_app.execute("""
                    INSERT INTO users (username, full_name, role_admin, role_doctor, role_visitor)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        full_name = VALUES(full_name),
                        role_admin = VALUES(role_admin),
                        role_doctor = VALUES(role_doctor),
                        role_visitor = VALUES(role_visitor)
                """, (username, full_name, 0, 1, 0))

                conn_app.commit()
                conn_app.close()
            except Exception as e:
                print(f"Error updating the users table: {str(e)}")

            return True, f"User {username} configured successfully with CRUD privileges"

        except pymysql.Error as e:
            return False, f"Error creating/modifying the user: {str(e)}"
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def update_user_privileges(username, privilege_type, host='%'):
        """
        Updates the privileges of an existing user

        Args:
            username: Name of the user to update
            privilege_type: Privilege type ('read_only', 'crud', 'admin')
            host: Host the user will be allowed to connect from

        Returns:
            tuple: (success, message)
        """
        if privilege_type not in UsersModel.PRIVILEGES:
            return False, f"Privilege type '{privilege_type}' is not valid"

        admin_credentials = UsersModel.get_admin_credentials()
        host_config = ConfigurationModel.load_configuration()

        try:
            # Connection using the administrator credentials
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password'],
                charset='utf8mb4'
            )
            cursor = conn.cursor()

            # Check whether the user exists
            cursor.execute("SELECT User FROM mysql.user WHERE User = %s", (username,))
            if not cursor.fetchone():
                return False, f"The user {username} does not exist"

            # Revoke the existing privileges (the regular ones first, then GRANT OPTION separately)
            cursor.execute(f"REVOKE ALL PRIVILEGES ON urgentix.* FROM '{username}'@'{host}'")
            try:
                # Revoke the global permissions
                cursor.execute(f"REVOKE {', '.join(UsersModel.ADMIN_GLOBAL_PRIVILEGES)} ON *.* FROM '{username}'@'{host}'")
            except pymysql.Error:
                # Ignore the errors if the user did not have these permissions
                pass

            try:
                # Revoke the permissions on the mysql database
                cursor.execute(f"REVOKE {', '.join(UsersModel.MYSQL_DB_PRIVILEGES)} ON mysql.* FROM '{username}'@'{host}'")
            except pymysql.Error:
                # Ignore the errors if the user did not have these permissions
                pass

            # Assign the new privileges
            if privilege_type == 'admin':
                cursor.execute(f"""
                    GRANT {', '.join(UsersModel.PRIVILEGES['admin'])} ON urgentix.* TO '{username}'@'{host}'
                    WITH GRANT OPTION
                """)

                # Add the global permissions for administrators (separately)
                cursor.execute(f"""
                    GRANT {', '.join(UsersModel.ADMIN_GLOBAL_PRIVILEGES)} ON *.* TO '{username}'@'{host}'
                """)

                # Specific permissions for the mysql database
                cursor.execute(f"""
                    GRANT {', '.join(UsersModel.MYSQL_DB_PRIVILEGES)} ON mysql.* TO '{username}'@'{host}'
                """)
            else:
                if privilege_type == 'read_only':
                    # Grant the basic read privileges (ONLY SELECT, SHOW VIEW)
                    cursor.execute(f"""
                        GRANT {', '.join(UsersModel.PRIVILEGES['read_only'])} ON urgentix.* TO '{username}'@'{host}'
                    """)
                else:
                    # For CRUD and other roles
                    privileges = UsersModel.PRIVILEGES[privilege_type]
                    cursor.execute(f"""
                        GRANT {', '.join(privileges)} ON urgentix.* TO '{username}'@'{host}'
                    """)

            cursor.execute("FLUSH PRIVILEGES")
            conn.commit()

            return True, f"Privileges of the user {username} updated to {privilege_type}"

        except pymysql.Error as e:
            return False, f"Error updating the privileges: {str(e)}"
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def create_admin_user(username, password, full_name, host='%'):
        """
        Creates a new user with administrator privileges

        Args:
            username: Username to create
            password: Password for the user
            full_name: Full name of the user
            host: Host the user will be allowed to connect from

        Returns:
            tuple: (success, message)
        """
        return UsersModel.create_user(username, password, full_name, host, is_admin=True)

    @staticmethod
    def deactivate_user(username):
        """
        Deactivates a user in the system and removes them from MySQL

        Args:
            username: Username to deactivate

        Returns:
            tuple: (success, message)
        """
        admin_credentials = UsersModel.get_admin_credentials()
        host_config = ConfigurationModel.load_configuration()

        try:
            # Connection used to update the status in the users table
            conn_app = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password'],
                database='urgentix',
                charset='utf8mb4'
            )
            cursor_app = conn_app.cursor()

            # Check whether the user exists and is active
            cursor_app.execute("""
                SELECT status FROM users WHERE username = %s
            """, (username,))

            result = cursor_app.fetchone()
            if not result:
                conn_app.close()
                return False, f"The user {username} does not exist in the database"

            if result[0] == 'inactive':
                conn_app.close()
                return False, f"The user {username} is already inactive"

            # Update the status to inactive in the users table
            cursor_app.execute("""
                UPDATE users SET status = 'inactive' WHERE username = %s
            """, (username,))

            conn_app.commit()
            conn_app.close()

            # Now delete the user from MySQL
            conn_mysql = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password'],
                charset='utf8mb4'
            )
            cursor_mysql = conn_mysql.cursor()

            # Delete the user from MySQL
            try:
                cursor_mysql.execute(f"DROP USER '{username}'@'%'")
                cursor_mysql.execute("FLUSH PRIVILEGES")
            except pymysql.Error as e:
                print(f"Error deleting the user from MySQL: {str(e)}")

            conn_mysql.commit()
            conn_mysql.close()

            return True, f"User {username} deactivated correctly and removed from the database"

        except Exception as e:
            return False, f"Error deactivating the user: {str(e)}"

    @staticmethod
    def change_password(username, new_password):
        """
        Changes the password of an existing user

        Args:
            username: Username whose password will be changed
            new_password: New password

        Returns:
            tuple: (success, message)
        """
        if not UsersModel.validate_password(new_password):
            return False, "The password does not meet the security requirements"

        admin_credentials = UsersModel.get_admin_credentials()
        host_config = ConfigurationModel.load_configuration()

        try:
            # Connection using the administrator credentials
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password'],
                charset='utf8mb4'
            )
            cursor = conn.cursor()

            # Check whether the user exists
            cursor.execute("SELECT User FROM mysql.user WHERE User = %s", (username,))
            if not cursor.fetchone():
                conn.close()
                return False, f"The user {username} does not exist"

            # Change the password
            cursor.execute(f"ALTER USER '{username}'@'%' IDENTIFIED BY '{new_password}'")
            cursor.execute("FLUSH PRIVILEGES")

            conn.commit()
            conn.close()

            return True, f"Password of the user {username} changed successfully"

        except pymysql.Error as e:
            return False, f"Error changing the password: {str(e)}"

    @staticmethod
    def validate_username(username):
        """
        Validates that the username meets the requirements:
        - Between 4 and 16 characters
        - Only letters, numbers and underscores
        - Does not start with a number

        Returns:
            bool: True if it is valid, False if not
        """
        if not username or len(username) < 4 or len (username) > 16:
            return False

        if not username[0].isalpha():
            return False

        return all(c.isalnum() or c == '_' for c in username)

    @staticmethod
    def validate_password(password):
        """
        Validates that the password meets the minimum requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character

        Returns:
            bool: True if it is valid, False if not
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
    def check_user_exists(username):
        """
        Checks whether a username already exists in the database

        Args:
            username: Username to check

        Returns:
            bool: True if the user exists, False if not
        """
        if not username:
            return False

        admin_credentials = UsersModel.get_admin_credentials()
        host_config = ConfigurationModel.load_configuration()

        try:
            # First we try to check in the users table
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password'],
                database='urgentix',
                charset='utf8mb4'
            )
            cursor = conn.cursor()

            # Check whether the user exists in the users table
            cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            exists = cursor.fetchone() is not None
            conn.close()

            if exists:
                return True

            try:
                # Create a connection using the root or administrator user
                conn = pymysql.connect(
                    host=host_config,
                    user=admin_credentials['user'],
                    password=admin_credentials['password'],
                    charset='utf8mb4'
                )
                cursor = conn.cursor()

                # Check the users
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.user_privileges
                    WHERE grantee LIKE %s
                """, (f"'%{username}%'",))

                count = cursor.fetchone()[0]
                conn.close()
                return count > 0

            except Exception as inner_e:
                print(f"Secondary error checking the user: {str(inner_e)}")
                # If both methods fail, we assume the user does not exist
                return False

        except Exception as e:
            print(f"Primary error checking the user: {str(e)}")
            return False

    @staticmethod
    def get_user_list():
        """
        Gets a list of every user in the database with their assigned roles
        from the 'users' table

        Returns:
            list: List of tuples (id, username, status, role) where:
                - id: numeric identifier of the user
                - username: name of the user
                - status: 'active' or 'inactive'
                - role: 'admin', 'doctor', 'visitor' or None
        """
        admin_credentials = UsersModel.get_admin_credentials()
        host_config = ConfigurationModel.load_configuration()

        try:
            # Connection using the administrator credentials
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password'],
                database='urgentix',
                charset='utf8mb4'
            )
            cursor = conn.cursor()

            # Get the list of every user in the table
            cursor.execute("""
                SELECT id, username, role_admin, role_doctor, role_visitor, status, full_name
                FROM users
                ORDER BY id
            """)

            local_users = {row[1]: row for row in cursor.fetchall()}

            # Get every active MySQL user
            cursor.execute("""
                SELECT User, Host FROM mysql.user
                WHERE User NOT IN ('root', 'mysql.sys', 'mysql.session', 'mysql.infoschema')
                AND User != ''
                ORDER BY User
            """)

            mysql_users = {user[0]: user for user in cursor.fetchall()}

            users = []
            temp_id = 10000  # Temporary ID for users with an error

            # First process the active MySQL users
            for username in mysql_users.keys():
                if username in local_users:
                    # The user exists in both places - they are active
                    user_data = local_users[username]
                    user_id = user_data[0]  # Use the real ID from the database
                    role_admin, role_doctor, role_visitor = user_data[2], user_data[3], user_data[4]
                    status = 'active'
                    full_name = user_data[6] or f"User {username}"

                    # If the status was inactive, update it to active
                    if user_data[5] != 'active':
                        cursor.execute("""
                            UPDATE users SET status = 'active'
                            WHERE username = %s
                        """, (username,))
                        conn.commit()

                    # Determine the main role
                    if role_admin:
                        role = 'admin'
                    elif role_doctor:
                        role = 'doctor'
                    elif role_visitor:
                        role = 'visitor'
                    else:
                        role = None
                else:
                    # The user exists in MySQL but not in the table - create an entry
                    is_admin = UsersModel.check_admin_role(username)
                    is_doctor = UsersModel.check_doctor_role(username)

                    # Determine the main role
                    if is_admin:
                        role = 'admin'
                        role_admin, role_doctor, role_visitor = 1, 0, 0
                    elif is_doctor:
                        role = 'doctor'
                        role_admin, role_doctor, role_visitor = 0, 1, 0
                    else:
                        role = 'visitor'
                        role_admin, role_doctor, role_visitor = 0, 0, 1

                    # Create an entry in the users table
                    try:
                        cursor.execute("""
                            INSERT INTO users (username, full_name, role_admin, role_doctor, role_visitor, status)
                            VALUES (%s, %s, %s, %s, %s, 'active')
                        """, (username, f"User {username}", role_admin, role_doctor, role_visitor))
                        conn.commit()

                        # Get the ID assigned in the database
                        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                        user_id = cursor.fetchone()[0]

                        status = 'active'
                        full_name = f"User {username}"
                    except Exception as e:
                        print(f"Error inserting the user into the users table: {str(e)}")
                        # Use a temporary ID if there is an error
                        user_id = temp_id
                        temp_id += 1
                        continue

                # Add to the user list using the real ID from the database
                users.append((user_id, username, status, role))

            # Now process the users in the table that no longer exist in MySQL
            for username, user_data in local_users.items():
                if username not in mysql_users:
                    # The user exists in the table but not in MySQL - mark as inactive
                    if user_data[5] == 'active':
                        cursor.execute("""
                            UPDATE users SET status = 'inactive'
                            WHERE username = %s
                        """, (username,))
                        conn.commit()

                    # Use the real ID from the database
                    user_id = user_data[0]

                    # Determine the main role
                    role_admin, role_doctor, role_visitor = user_data[2], user_data[3], user_data[4]
                    if role_admin:
                        role = 'admin'
                    elif role_doctor:
                        role = 'doctor'
                    elif role_visitor:
                        role = 'visitor'
                    else:
                        role = None

                    # Add to the user list with an inactive status
                    users.append((user_id, username, 'inactive', role))

            conn.close()
            return users

        except Exception as e:
            print(f"Error getting the user list: {str(e)}")
            return []

    @staticmethod
    def update_roles_in_table(username, role):
        """
        Updates the roles in the users table to keep them consistent

        Args:
            username: Username to update
            role: Assigned role ('admin', 'doctor', 'visitor')

        Returns:
            bool: True if it was updated correctly, False otherwise
        """
        try:
            admin_credentials = UsersModel.get_admin_credentials()
            host_config = ConfigurationModel.load_configuration()

            # Default values for the roles
            admin_val = 0
            doctor_val = 0
            visitor_val = 0

            # Set the values according to the assigned role
            if role == 'admin':
                admin_val = 1
            elif role == 'crud':
                doctor_val = 1
            elif role == 'read_only':
                visitor_val = 1

            # Connection using the administrator credentials
            conn = pymysql.connect(
                host=host_config,
                user=admin_credentials['user'],
                password=admin_credentials['password'],
                database='urgentix',
                charset='utf8mb4'
            )
            cursor = conn.cursor()

            # Check whether the user exists in the table
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user_exists = cursor.fetchone() is not None

            if user_exists:
                # Update the roles of the existing user
                cursor.execute("""
                    UPDATE users
                    SET role_admin = %s, role_doctor = %s, role_visitor = %s
                    WHERE username = %s
                """, (admin_val, doctor_val, visitor_val, username))
            else:
                # Insert a new user with roles
                cursor.execute("""
                    INSERT INTO users (username, full_name, role_admin, role_doctor, role_visitor, status)
                    VALUES (%s, %s, %s, %s, %s, 'active')
                """, (username, f"User {username}", admin_val, doctor_val, visitor_val))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"Error updating the roles in the users table: {str(e)}")
            return False

    @staticmethod
    def check_admin_role(username):
        """
        Checks whether a user has the administrator role
        by querying the users table directly

        Args:
            username: Name of the user to check

        Returns:
            bool: True if they have the administrator role, False otherwise
        """
        return UsersModel.get_user_role(username) == 'admin'

    @staticmethod
    def check_doctor_role(username):
        """
        Checks whether a user has the doctor role
        by querying the users table directly

        Args:
            username: Name of the user to check

        Returns:
            bool: True if they have the doctor role, False otherwise
        """
        return UsersModel.get_user_role(username) == 'doctor'

    @staticmethod
    def connect_db():
        """Establishes a connection to the database"""
        try:
            host_config = ConfigurationModel.load_configuration()

            # Use the credentials of the currently authenticated user from AuthenticationModel
            from backend.database import AuthenticationModel
            credentials = AuthenticationModel.get_credentials()

            # If there are no credentials available, use admin_credentials as a fallback
            if not credentials.get('user') or not credentials.get('password'):
                admin_credentials = UsersModel.get_admin_credentials()
                conn = pymysql.connect(
                    host=host_config,
                    user=admin_credentials['user'],
                    password=admin_credentials['password'],
                    database='urgentix',
                    charset='utf8mb4'
                )
            else:
                # Use the credentials of the authenticated user
                conn = pymysql.connect(
                    host=host_config,
                    user=credentials['user'],
                    password=credentials['password'],
                    database='urgentix',
                    charset='utf8mb4'
                )
            return conn
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return None

    @staticmethod
    def get_user_role(username):
        """
        Gets the role of a user directly from the users table.

        Args:
            username: Username

        Returns:
            str: The role of the user ('admin', 'doctor', 'visitor') or 'visitor' by default
        """
        if not username:
            return 'visitor'  # Default role if no username provided

        try:
            # Connection to the DB
            conn = UsersModel.connect_db()
            if not conn:
                return 'visitor'  # Default role if connection fails

            cursor = conn.cursor()

            # Query the values of the user's roles
            cursor.execute("""
                SELECT role_admin, role_doctor, role_visitor
                FROM users
                WHERE username = %s
            """, (username,))

            result = cursor.fetchone()
            conn.close()

            # If the user exists in the table, determine their main role
            if result:
                role_admin, role_doctor, role_visitor = result

                if role_admin:
                    return 'admin'
                elif role_doctor:
                    return 'doctor'
                elif role_visitor:
                    return 'visitor'
                else:
                    return 'visitor'  # Default to visitor if no role is set

            # If they are not in the users table, try to detect the privileges and create them
            # This is a recovery case for legacy users
            try:
                # Create a default entry with the visitor role for this user
                UsersModel.update_roles_in_table(username, 'read_only')
                return 'visitor'
            except:
                return 'visitor'  # If the creation fails, assign visitor by default

        except Exception as e:
            print(f"Error getting the user role: {str(e)}")
            return 'visitor'