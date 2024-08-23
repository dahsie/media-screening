import numpy as np
import pandas as pd
import sys
from google.cloud import translate
sys.path.append("../src/utils")
from utils import split_liste, create_logger

logger = create_logger(__name__, 'googletranslator.log')

class GoogleTranslate :
    """
    A class to handle translation tasks using the Google Cloud Translation API.

    Attributes
    ----------
        __client (translate.TranslationServiceClient): The Google Cloud Translation API client.
        __parent (str): The resource name of the Google Cloud project.
        __target_language_code (str): The target language code for translation.
        __fails_index (list[int]): A list to keep track of indices where translation failed.

    Methods
    --------
        __init__(self, project_id: str, location: str = "global", target_language_code: str = "en"):
            Initializes the GoogleTranslate class with the given project ID, location, and target language code.
            
        __validate_target_language_code(self, language_code: str) -> bool:
            Validates the target language code to ensure it is a non-null string of length 2.
            
        __translate_text(self, texts: list[list[str]], source_language_code: str) -> list[str]:
            Translates the provided texts from the source language to the target language.
    
        translation(self, dataframe: pd.DataFrame, limit: int = 30720) -> pd.DataFrame:
            Translates the 'title' and 'text' columns of a given DataFrame from the source language to the target language.
            
        fails_index(self) -> list[int]:
            Returns the list of indices where translation failed.
        """
    
    def __init__(self, project_id : str, location : str = "global", target_language_code: str = "en"):
        
        """
        Initializes the GoogleTranslate class with the given project ID, location, and target language code.

        Args:
            project_id (str): The Google Cloud project ID.
            location (str, optional): The location of the Google Cloud project. Defaults to "global".
            target_language_code (str, optional): The target language code for translation. Defaults to "en".

        Raises:
            ValueError: If the target language code is invalid.
        """
        
        self.__client = translate.TranslationServiceClient()
        self.__parent = f"projects/{project_id}/locations/{location}"
        _ = self.__validate_target_language_code(target_language_code)
        self.__target_language_code = target_language_code
        self.__fails_index : list[int] = []
        
    def __validate_target_language_code(self,language_code: str) -> bool:
        """
        Validates the target language code.

        Args:
            language_code (str): The language code to validate.

        Raises:
            ValueError: If the language code is invalid.

        Returns:
            bool: True if the language code is valid.
        """
        
        if language_code is None :
            error_message = "Language code must not be None."
            logger.error(error_message)
            raise ValueError(error_message)
            
        elif not isinstance(language_code, str) :
            error_message = f"Language code must be a string, got {type(language_code).__name__} instead."
            logger.error(error_message)
            raise ValueError(error_message)
            
        elif len(language_code) != 2 :
            error_message = f"Language code must be exactly 2 characters long, got {len(language_code)} characters."
            logger.error(error_message)
            raise ValueError(error_message)
            
        logger.info(f"Validated target language code: {language_code}")
    
        return True
        
    def __translate_text(self, texts: list[list[str]],  source_language_code : str) -> translate.TranslationServiceClient:
        """
        Translates text from the source language to the target language.

        Args:
            texts (list[list[str]]): The texts to translate.
            source_language_code (str): The source language code.

        Returns:
            list[str]: The translated texts.
        """
        
        request={"parent": self.__parent,
                "contents": None,
                "mime_type": "text/plain",  # mime types: text/plain, text/html
                "source_language_code":source_language_code,
                "target_language_code": self.__target_language_code}
        
        responses = []
        
        for list_of_text in texts : # list_of_text itself is a list of text while text is a list of list of text
            
            request["contents"] = list_of_text
            response = self.__client.translate_text(**request)
            responses += [translation.translated_text for translation in response.translations]
        
        logger.info("Texts successfully translated.")
        return responses
    
    def translation(self, dataframe : pd.DataFrame, limit : int =30720):
        """
        Translates the 'title' and 'text' columns of a given DataFrame from the source language to the target language.

        Args:
            dataframe (pd.DataFrame): The DataFrame containing text to be translated. Must contain 'title', 'text', and 'lang' columns.
            limit (int, optional): The token limit for splitting text. Defaults to 30720.

        Returns:
            pd.DataFrame: The DataFrame with translated text.

        Raises:
            ValueError: If the DataFrame does not contain the required columns.
        """
        
        required_columns = {'title', 'text', 'lang'}
        # Check if the DataFrame contains the required columns
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

            data_ = data_.loc[data_['title'] !='',:] if data_ is not None and len(data_) !=0  else None
            data_ = data_.loc[data_['text'] !='',:] if data_ is not None and  len(data_) !=0 else None
            data_ = data_.loc[data_['text'].str.len() < limit, :] if data_ is not None and  len(data_) !=0 else None
            
            if data_ is None or len(data_) == 0:
                continue
            logger.info(f" data_.shape :{ data_.shape}")
            
            # Translating title
            sub1 = split_liste(list(data_['title']), limit=limit)
            try :
                titles = self.__translate_text(texts =sub1, source_language_code=lang)
                data_['translated_title'] = titles
            except Exception as e :
                logger.error(e)
                self.__fails_index += list(data_.index)
                continue

            ## Translating text
            sub = split_liste(list(data_['text']), limit=limit)
            try :
                texts =self.__translate_text(texts =sub, source_language_code=lang)
                data_['translated_text'] = texts
            except Exception as e :
                logger.error(e)
                self.__fails_index += list(data_.index)
                continue
            
            news_dataframe = pd.concat([news_dataframe, data_], axis=0)
        
        logger.info("Translation of DataFrame completed.")
        return news_dataframe
    
    @property
    def fails_index(self):
        return self.__fails_index
    
        