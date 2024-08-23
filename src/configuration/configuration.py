from deep_translator import GoogleTranslator
import json
import logging
from typing import Tuple, Optional, Union, List, Dict
import sys
sys.path.append("../src/utils/")

from utils import create_logger

logger = create_logger(__name__, 'configuration.log')

class Configuration:
    """
    A class to handle and manage configuration settings for news translation and country-language pairs.

    This class loads a JSON configuration file, validates the country and language codes, translates
    the specified keywords for each language, and generates configurations for news queries.

    Attributes
    ----------
        file_path (str): Path to the JSON configuration file.
        __config (dict): The loaded configuration data.
        __country_lang_dict (list): List of country-language configurations.
        __translator (GoogleTranslator): Translator object for keyword translation.

    Methods
    -------
        __read_json(config_file: str) -> Dict:
            Reads and returns the content of the JSON configuration file.
        
        __validate_news_config():
            Validates and normalizes country and language codes in the configuration.
        
        __translate_keywords(lang: str) -> str:
            Translates keywords into the specified language.
        
        __news_config():
            Generates configurations for each country-language pair, translating keywords and storing results.
        
        get_config() -> List[Dict[str, str]]:
            Returns the list of generated configurations.

    Example
    -------
        to add
    """
    def __init__(self, initial_config_file : str, final_config_file: str):
        """
        Initializes the Configuration object by loading the configuration file and setting up
        the translator.

        Args:
            config_file (str): Path to the JSON configuration file.

        Raises:
            ValueError: If the configuration contains invalid country or language codes.
        """
        logger.info(f"Initializing Configuration with file: {initial_config_file}")
        self.initial_config_file = initial_config_file
        self.final_config_file = final_config_file
        self.__config =self.__read_json(initial_config_file = initial_config_file)
        self.__country_lang_dict = self.__config['country_lang']
        self.__translator = GoogleTranslator(source= "auto",target="en")

        self.__validate_news_config()
        self.__news_config()
   
    
    def __read_json(self, initial_config_file) :
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
            logger.info(f"Reading JSON configuration file: {initial_config_file}")
            with open(initial_config_file, 'r') as file :
                json_data = json.load(file)
            return json_data
        except FileNotFoundError as e :
            logger.error(f"File {initial_config_file} not found.")
            print(f"File {initial_config_file} not found, provide a correct file path.")
        except:
            # Others exceptiopns to add and handle
            pass
        
    def __validate_news_config(self):
        """
        Validates and normalizes the country and language codes in the configuration.

        Raises:
            ValueError: If any country or language code is invalid.
        """
        for index, config in enumerate(self.__country_lang_dict):
            country_code = config.get('country')
            lang_code = config.get('lang')
            # print(config)
            
            if not isinstance(country_code, str) or len(country_code) != 2:
                logger.error(f"Invalid country code: {country_code}")
                raise ValueError(f"Invalid country code: {country_code}")
            
            list_lang = []
            
            for lang in lang_code :
                if not isinstance(lang, str) or len(lang) != 2:
                    logger.error(f"Invalid language code: {lang_code}")
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
        except KeyError as ke :
            logger.error("`self.__config` does not contain the key 'keywords'. Please check the configuration file.")
            raise ke
        except Exception as e:
            logger.error(f"Translation failed for language {lang}: {e}")
            raise e
            # Error to handle

    def __news_config(self):
        """
        Generates configurations for each country-language pair, translating the keywords
        and storing the results.
        """
        logger.info("Generating news configurations.")
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
        
        logger.info("News configurations generated successfully.")
        
        with open(self.final_config_file, 'w') as file :
            logger.info(f"config save to path : {self.final_config_file}")
            json.dump(self.__config, file, indent = 4)

    def get_config(self) -> List[Dict[str, str]]:
        """
        Returns the of generated configurations.

        Returns:
            Dict: List of configurations with country, lang, and translated query.
        """
        logger.info("Returning generated configurations.")
        return self.__config
