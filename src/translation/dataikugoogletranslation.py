
import dataiku
import numpy as np
import pandas as pd

import logging
import requests
import html

from media.src.utils.utils import create_logger, split_liste


logger = create_logger(__name__, 'dataikugoogletranslator.log')


class DataikuGoogleTranslate:
    """
    A class to handle translation tasks using the Google Cloud Translation API.

    Attributes
    ----------
    __api_key : str
        The API key for authenticating requests to the Google Cloud Translation API.
    __base_url : str
        The base URL for the Google Cloud Translation API.
    __target_language_code : str
        The target language code for translation.
    __fails_index : list[int]
        A list to keep track of indices where translation failed.

    Methods
    -------
    __init__(self, api_key: str, target_language_code: str = "en", base_url: str = "https://translation.googleapis.com/language/translate/v2"):
        Initializes the GoogleTranslate class with the given API key, target language code, and base URL.

    __validate_target_language_code(self, language_code: str) -> bool:
        Validates the target language code to ensure it is a non-null string of exactly 2 characters.

    __postprocess_translation(self, translated_text: str) -> str:
        Decodes HTML entities in the translated text.

    __translate_text(self, texts: list[list[str]], source_language_code: str) -> list[str]:
        Translates the provided texts from the source language to the target language using the Google Cloud Translation API.

    translation(self, dataframe: pd.DataFrame, language_limits: dict) -> pd.DataFrame:
        Translates the 'title' and 'text' columns of a given DataFrame from the source language to the target language.
    """

    def __init__(self, api_key: str, target_language_code: str = "en", base_url: str = "https://translation.googleapis.com/language/translate/v2"):
        """
        Initializes the GoogleTranslate class with the given API key, target language code, and base URL.

        Args:
            api_key (str): The API key for authenticating requests to the Google Cloud Translation API.
            target_language_code (str, optional): The target language code for translation. Defaults to "en".
            base_url (str, optional): The base URL for the Google Cloud Translation API. Defaults to "https://translation.googleapis.com/language/translate/v2".

        Raises:
            ValueError: If the target language code is invalid.
        """
        self.__api_key = api_key
        self.__base_url = base_url
        _ = self.__validate_target_language_code(target_language_code)
        self.__target_language_code = target_language_code
        self.__fails_index: list[int] = []

    def __validate_target_language_code(self, language_code: str) -> bool:
        """
        Validates the target language code.

        Args:
            language_code (str): The language code to validate.

        Raises:
            ValueError: If the language code is invalid.

        Returns:
            bool: True if the language code is valid.
        """
        if language_code is None:
            error_message = "Language code must not be None."
            logger.error(error_message)
            raise ValueError(error_message)
        elif not isinstance(language_code, str):
            error_message = f"Language code must be a string, got {type(language_code).__name__} instead."
            logger.error(error_message)
            raise ValueError(error_message)
        elif len(language_code) != 2:
            error_message = f"Language code must be exactly 2 characters long, got {len(language_code)} characters."
            logger.error(error_message)
            raise ValueError(error_message)

        logger.info(f"Validated target language code: {language_code}")
        return True

    def __postprocess_translation(self, translated_text: str) -> str:
        """
        Decodes HTML entities in a translated text.

        Args:
            translated_text (str): The translated text potentially containing HTML entities.

        Returns:
            str: The text with HTML entities decoded.
        """
        return html.unescape(translated_text)

    def translate_liste(self,list_of_text: list[str], params: dict): 
        
        params['q'] = list_of_text
        response = requests.post(self.__base_url, params=params)

        if response.status_code == 411:
            logger.error("Texts were not translated successfully. The number of characters exceeded the translation limit. Please inspect the portion of the text you are trying to translate and specify the correct character limit. The limit may vary depending on the language code.")
            print("*"*40)
            print("*"*40)
            print("Texts were not translated successfully. The number of characters exceeded the translation limit. Please inspect the portion of the text you are trying to translate and specify the correct character limit. The limit may vary depending on the language code.")
            print(f"params['source'] = {params['source']}")
            print("*"*40)
            print("*"*40)
        elif response.status_code == 200:
            response = response.json()
            print("*"*40)
            print("*"*40)
            print("success")
            print("*"*40)
            print("*"*40)
            processed_response = [self.__postprocess_translation(item['translatedText']) for item in response['data']['translations']]
        else :
            logger.error(f"Unknown error with status code = {response.status_code }")
            print("*"*40)
            print("*"*40)
            print(f"Unknown error with status code = {response.status_code }")
            print(f"params['source'] = {params['source']}")
            print("*"*40)
            print("*"*40)
        return processed_response
        
    def __translate_text(self, texts: list[list[str]], source_language_code: str) -> list[str]:
        """
        Translates text from the source language to the target language.

        Args:
            texts (list[list[str]]): The texts to translate.
            source_language_code (str): The source language code.

        Returns:
            list[str]: The translated texts.
        """
        params = {
            "q": None,
            "source": source_language_code,
            "target": self.__target_language_code,
            "key": self.__api_key
        }

        responses = []

        for list_of_text in texts:  # list_of_text itself is a list of text while texts is a list of lists of text
            processed_response = self.translate_liste(list_of_text = list_of_text, params = params)
            responses += processed_response
            logger.info("Texts successfully translated.")
        return responses

    def translation(self, dataframe: pd.DataFrame, language_limits: dict) -> pd.DataFrame:
        """
        Translates the 'title' and 'text' columns of a given DataFrame from the source language to the target language.

        Args:
            dataframe (pd.DataFrame): The DataFrame containing text to be translated. Must contain 'title', 'text', and 'lang' columns.
            language_limits (dict): A dictionary mapping language codes to their respective character limits.

        Returns:
            pd.DataFrame: The DataFrame with translated text.

        Raises:
            ValueError: If the DataFrame does not contain the required columns.
        """
        required_columns = {'titles', 'texts', 'lang'}
        if not required_columns.issubset(dataframe.columns):
            missing_columns = required_columns - set(dataframe.columns)
            logger.error(f"The DataFrame is missing the following required columns: {', '.join(missing_columns)}")
            raise ValueError(f"The DataFrame is missing the following required columns: {', '.join(missing_columns)}")

        logger.info("Starting translation of DataFrame.")
        news_dataframe = dataframe.loc[dataframe['lang'] == self.__target_language_code, :]
        remain_dataframe = dataframe.loc[dataframe['lang'] != self.__target_language_code, :]

        langs = list(np.unique(remain_dataframe['lang']))

        for index, lang in enumerate(langs):
            data_ = remain_dataframe.loc[remain_dataframe['lang'] == lang, :]
            limit = language_limits[lang]
            data_ = data_.loc[data_['titles'] != '', :] if data_ is not None and len(data_) != 0 else None
            data_ = data_.loc[data_['texts'] != '', :] if data_ is not None and len(data_) != 0 else None

            if data_ is None or len(data_) == 0:
                continue
            logger.info(f" data_.shape :{data_.shape}")
            logger.info(f" language code  :{lang}")

            ## Translating title
            sub1 = split_liste(list(data_['titles']), limit=limit)
            print("*"*40)
            print("*"*40)
            print(f"language_limits[lang] = {language_limits[lang]}")
            print("*"*40)
            print("*"*40)
            titles = self.__translate_text(texts=sub1, source_language_code=lang)

            data_['translated_title'] = titles

            ## Translating text
            sub = split_liste(list(data_['texts']), limit=limit)
            texts = self.__translate_text(texts=sub, source_language_code=lang)
            data_['translated_text'] = texts

            news_dataframe = pd.concat([news_dataframe, data_], axis=0)
        logger.info("Translation of DataFrame completed.")
        return news_dataframe
    #---------------------------------- PROPERTIES ---------------------------------------------------------
    @property
    def fails_index(self):
        return self.__fails_index

    @property
    def target_language_code(self):
        return self.__target_language_code

    @property
    def base_url(self):
        return self.__base_url
    
