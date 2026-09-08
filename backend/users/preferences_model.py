import json
import os
import sys

class PreferencesModel:
    """
    Model for handling user preferences, including area filters
    and other custom settings, using JSON files.
    """

    # Class variable that stores preferences in memory during the session
    _preferences_cache = {}

    @staticmethod
    def get_preferences_path():
        """Gets the path where the preferences will be saved as a file"""
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Create the 'preferences' folder if it does not exist
        preferences_path = os.path.join(base_path, 'preferences')
        if not os.path.exists(preferences_path):
            try:
                os.makedirs(preferences_path)
            except Exception as e:
                print(f"Could not create the preferences directory: {str(e)}")
                import tempfile
                preferences_path = tempfile.gettempdir()

        return preferences_path

    @staticmethod
    def save_filter_preferences(username, filtered_areas):
        """
        Saves the area filter preferences for a user in a JSON file.

        Args:
            username: User the preferences belong to
            filtered_areas: List of selected areas

        Returns:
            bool: True if it was saved correctly, False otherwise
        """
        if not username:
            return False

        # Save in the memory cache for the current session
        if username not in PreferencesModel._preferences_cache:
            PreferencesModel._preferences_cache[username] = {}

        PreferencesModel._preferences_cache[username]['area_filters'] = filtered_areas

        # Save to a JSON file
        try:
            # Get the file path
            preferences_path = PreferencesModel.get_preferences_path()
            preferences_file = os.path.join(preferences_path, f"{username}_prefs.json")

            # Create or load the current content
            preferences = {}
            if os.path.exists(preferences_file):
                try:
                    with open(preferences_file, 'r') as f:
                        preferences = json.load(f)
                except:
                    preferences = {}

            # Update the filters
            preferences['area_filters'] = filtered_areas

            # Save to the file
            with open(preferences_file, 'w') as f:
                json.dump(preferences, f)

            print(f"Preferences saved to file: {preferences_file}")
            return True
        except Exception as e:
            print(f"Error saving preferences to file: {str(e)}")
            return False

    @staticmethod
    def get_area_filters(username, available_areas):
        """
        Gets the area filter preferences for a user.
        Tries the memory cache first, then the file.

        Args:
            username: User whose preferences will be retrieved
            available_areas: List of areas available by default

        Returns:
            list: List of filtered areas according to the user's preferences
        """
        if not username:
            return available_areas

        # Check the memory cache first (for the current session)
        if (username in PreferencesModel._preferences_cache and
            'area_filters' in PreferencesModel._preferences_cache[username]):
            cached_filters = PreferencesModel._preferences_cache[username]['area_filters']
            # Validate the cached areas
            valid_filters = [area for area in cached_filters if area in available_areas]
            if valid_filters:
                print(f"Using cached filters for {username}")
                return valid_filters

        # Try to get them from the file
        try:
            preferences_path = PreferencesModel.get_preferences_path()
            preferences_file = os.path.join(preferences_path, f"{username}_prefs.json")

            if os.path.exists(preferences_file):
                try:
                    with open(preferences_file, 'r') as f:
                        preferences = json.load(f)

                    if 'area_filters' in preferences and preferences['area_filters']:
                        # Validate that the areas exist
                        valid_filters = [area for area in preferences['area_filters']
                                          if area in available_areas]

                        if valid_filters:
                            # Update the cache
                            if username not in PreferencesModel._preferences_cache:
                                PreferencesModel._preferences_cache[username] = {}
                            PreferencesModel._preferences_cache[username]['area_filters'] = valid_filters

                            print(f"Using filters from file for {username}")
                            return valid_filters
                except Exception as e:
                    print(f"Error loading preferences from file: {str(e)}")
        except Exception as e:
            print(f"Error accessing the preferences file: {str(e)}")

        # If no preferences are found, return every area
        print(f"No saved filters found for {username}, using the default areas")
        return available_areas

    @staticmethod
    def save_pagination_interval(username, seconds):
        """
        Saves the pagination interval preference for a user.

        Args:
            username: User the preference belongs to
            seconds: Time in seconds between page changes

        Returns:
            bool: True if it was saved correctly, False otherwise
        """
        if not username:
            return False

        # Save in the memory cache for the current session
        if username not in PreferencesModel._preferences_cache:
            PreferencesModel._preferences_cache[username] = {}

        PreferencesModel._preferences_cache[username]['pagination_interval'] = seconds

        # Save to a JSON file
        try:
            preferences_path = PreferencesModel.get_preferences_path()
            preferences_file = os.path.join(preferences_path, f"{username}_prefs.json")

            # Create or load the current content
            preferences = {}
            if os.path.exists(preferences_file):
                try:
                    with open(preferences_file, 'r') as f:
                        preferences = json.load(f)
                except:
                    preferences = {}

            # Update the pagination interval
            preferences['pagination_interval'] = seconds

            # Save to the file
            with open(preferences_file, 'w') as f:
                json.dump(preferences, f)

            print(f"Pagination interval saved to file: {preferences_file}")
            return True
        except Exception as e:
            print(f"Error saving the pagination interval: {str(e)}")
            return False

    @staticmethod
    def get_pagination_interval(username, default_value=5):
        """
        Gets the pagination interval preference for a user.

        Args:
            username: User whose preferences will be retrieved
            default_value: Value to return if there is no saved preference

        Returns:
            int: Time in seconds between page changes
        """
        if not username:
            return default_value

        # Check the memory cache first
        if (username in PreferencesModel._preferences_cache and
            'pagination_interval' in PreferencesModel._preferences_cache[username]):
            return PreferencesModel._preferences_cache[username]['pagination_interval']

        # Try to get it from the file
        try:
            preferences_path = PreferencesModel.get_preferences_path()
            preferences_file = os.path.join(preferences_path, f"{username}_prefs.json")

            if os.path.exists(preferences_file):
                try:
                    with open(preferences_file, 'r') as f:
                        preferences = json.load(f)

                    if 'pagination_interval' in preferences:
                        interval = preferences['pagination_interval']

                        # Update the cache
                        if username not in PreferencesModel._preferences_cache:
                            PreferencesModel._preferences_cache[username] = {}
                        PreferencesModel._preferences_cache[username]['pagination_interval'] = interval

                        print(f"Using the pagination interval from file: {interval}s")
                        return interval
                except Exception as e:
                    print(f"Error loading the pagination interval: {str(e)}")
        except Exception as e:
            print(f"Error accessing the preferences file: {str(e)}")

        # If no preference is found, return the default value
        print(f"No pagination interval found for {username}, using the default value: {default_value}s")
        return default_value
