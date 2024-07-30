from deep_translator import GoogleTranslator
import json
import logging
from typing import Tuple, Optional, Union, List, Dict


class Configuration:
    
    def __init__(self, config_file : str):
        """
        Initializes the Configuration object by loading the configuration file and setting up
        the translator.

        Args:
            config_file (str): Path to the JSON configuration file.

        Raises:
            ValueError: If the configuration contains invalid country or language codes.
        """
        self.file_path = config_file
        self.__config =self.__read_json(config_file)
        self.__country_lang_dict = self.__config['country_lang']
        self.__translator = GoogleTranslator(source= "auto",target="en")

        self.__validate_news_config()
        self.__news_config()
   
    
    def __read_json(self, config_file) :
        """
        Reads a JSON file and returns its content.

        Args:
            config_file (str): Path to the JSON file.
            
        Returns:
            Dict: The content of the JSON file.
            
        Raises:
            FileNotFoundError: If the specified file does not exist.
        """
        try :
            with open(config_file, 'r') as file :
                json_data = json.load(file)
            return json_data
        except FileNotFoundError as e :
            print(f"File {config_file} not found, provide a correct file path.")
            # Error handle here
            
    def __validate_news_config(self):
        """
        Validates and normalizes the country and language codes in the configuration.

        Raises:
            ValueError: If any country or language code is invalid.
        """
        for index, config in enumerate(self.__country_lang_dict):
            country_code = config.get('country')
            lang_code = config.get('lang')

            if not isinstance(country_code, str) or len(country_code) != 2:
                raise ValueError(f"Invalid country code: {country_code}")
            
            list_lang = []
            for lang in lang_code :
                if not isinstance(lang, str) or len(lang) != 2:
                    raise ValueError(f"Invalid language code: {lang_code}")
                list_lang.append(lang.lower())

            self.__country_lang_dict[index]['country'] = country_code.upper()
            self.__country_lang_dict[index]['lang'] = list_lang



    def __translate_keywords(self, lang: str) -> str:
        """
        Translates the keywords into the specified language.

        Args:
            lang (str): The language code for the translation.

        Returns:
            str: The translated keywords.

        Raises:
            KeyError: If the configuration does not contain the 'keywords' key.
            Exception: If the translation fails for any other reason.
        """
        try:
            self.__translator.target = lang
            keywords = self.__config['keywords'] if isinstance(self.__config['keywords'], list) else [self.__config['keywords']]
            translation = self.__translator.translate_batch(keywords)
            return translation
        except KeyError as e :
            print(" `self.config' does not conatin this key `keywords`. Please cheick that you provide the right config file with the right keys")
        except Exception as e:
            print(f"Translation failed for language {lang}: {e}")
            # Error to handle

    def __news_config(self):
        """
        Generates configurations for each country-language pair, translating the keywords
        and storing the results.
        """
        news_configs =[]
        for item in self.__country_lang_dict:
            
            for lang in item['lang'] :
                translated_keywords = self.__translate_keywords(lang)
                news_configs.append({
                    'country': item['country'],
                    'lang': lang,
                    'queries': translated_keywords
                })
        self.__config['country_lang'] = news_configs

    def get_config(self) -> List[Dict[str, str]]:
        """
        Returns the of generated configurations.

        Returns:
            Dict: List of configurations with country, lang, and translated query.
        """
        return self.__config
