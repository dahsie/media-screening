
import dataiku
import numpy as np
import pandas as pd

import logging
import requests
import html
from typing import Tuple

from media.src.utils.utils import create_logger

logger, logfile_path = create_logger(__name__, 'dataikugoogletranslator.log')


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
        self.logfile_path  = logfile_path

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

    def split_text(self,text, length)-> list:
        """
        Splits the input text into smaller chunks, each with a maximum length, 
        ensuring that it breaks at punctuation or newlines for better readability.

        Args:
            text (str): The input text to be split.
            length (int): The maximum length for each chunk of text.

        Returns:
            list: A list of text chunks, where each chunk's length is less than or equal to the specified limit.
        """
       
        if len(text) < length :
            return [text]

        sous_chaines = []
        while len(text) > length:
            pos = length
            while pos > 0 and text[pos] not in ['.', '!', '?', '\n', '\n\n']:
                pos -= 1
            pos += 1 #One include the ponctuation sign within the sub-string
            sous_chaines.append(text[:pos])
            text = text[pos:]
        sous_chaines.append(text)
        return sous_chaines
    
    def html_decoder(self, translated_text: str) -> str:
        """
        Decodes HTML entities in a translated text.

        Args:
            translated_text (str): The translated text potentially containing HTML entities.

        Returns:
            str: The text with HTML entities decoded.
        """
        return html.unescape(translated_text)
    
    
    def group_list(self, ids: list[list[int]], texts: list[list[str]]) -> Tuple[list[list[int]], list[list[str]]]:
        """
        Groups consecutive identical elements in the 'ids' list and merges their corresponding texts.

        Args:
            ids (list[list[int]]): A list of lists containing integer IDs.
            texts (list[list[str]]): A list of lists containing the corresponding texts.

        Returns:
            Tuple[list[list[int]], list[list[str]]]: Two lists of lists - 
            one with grouped IDs and the other with the combined texts.
        """
        new_ids = []
        new_texts = []

        # Parcourir la liste et regrouper les éléments consécutifs identiques
        for index, sub_list in enumerate(ids):
            # Si la liste est vide ou que le premier élément du dernier groupe est différent
            if not new_ids or new_ids[-1][0] != sub_list[0]:
                new_ids.append(sub_list)
                new_texts.append(texts[index])
            else:
                # Si le premier élément est le même, on fusionne les sous-listes
                new_ids[-1].extend(sub_list)
                new_texts[-1].extend(texts[index])
        logger.info("group_list succesfully!")
        return new_ids, new_texts

    def contenate_list(self, ids: list[list[int]], texts: list[list[str]]) ->Tuple[list[int], list[str]] :
        """
        Concatenates texts based on unique IDs. For consecutive identical IDs, 
        the corresponding texts are merged. For non-identical IDs, the texts remain separate.

        Args:
            ids (list[list[int]]): A list of lists containing integer IDs.
            texts (list[list[str]]): A list of lists containing the corresponding texts.

        Returns:
            Tuple[list[int], list[str]]: A list of concatenated texts with corresponding unique IDs.
        """
        new_ids =[]
        new_texts = []
        for index, item in enumerate(ids):
            if len(np.unique(item)) == 1:
                new_texts.append(" ".join(texts[index]))
                new_ids.append(item[0])
            else:
                for index1, identifier in enumerate(ids[index]):
                    new_texts.append(texts[index][index1])
                    new_ids.append(identifier)
                    
        logger.info("concatenate succesfully!")
        return new_ids, new_texts

    def reorder_texts(self,ids : list[int], texts: list[str]) ->list[str]:
        """
        Reorders the 'texts' list based on the ascending order of 'ids'.

        Args:
            ids (list[int]): A list of integer IDs.
            texts (list[str]): A list of corresponding texts.

        Returns:
            list[str]: A list of texts reordered by the IDs.
        """
        df = pd.DataFrame({
            "ids" : ids,
            "texts": texts
        })
        
        df.sort_values(by = "ids", ascending = True, inplace=True)
        
        logger.info("reorder succesfully!")
        return list(df['texts']), df
    
    
    def __postprocess_translation(translated_text: str) -> str:
        """
        Decodes HTML entities in a translated text.

        Args:
            translated_text (str): The translated text potentially containing HTML entities.

        Returns:
            str: The text with HTML entities decoded.
        """
        return html.unescape(translated_text)
    
    def split_liste(self, texts : list[str], limit : int , separators: list[str] = ['.', '!', '?', '\n', '\n\n'])-> list[list[str]]:
        """
        Splits a list of texts into sub-lists based on a token limit, using specified separators.

        Args:
            texts (list[str]): The texts to split.
            limit (int): The token limit for each sub-list.
            separators (list[str], optional): The list of separators to use for splitting the texts. Defaults to ['.', '!', '?', '\n', '\n\n'].

        Returns:
            list[list[str]]: A list of sub-lists containing the split texts.

        Raises:
            ValueError: If a single text exceeds the token limit after splitting.
        """
        # logger.info("Splitting texts into sub-lists with a limit of %d tokens", limit)

        sub_list = []
        liste = []
        cpt = 0
        ids = []
        sub_ids = []
        for identifier, text in enumerate(texts):

            length_text = len(text)

            if length_text >= limit :
                chunks_ = self.split_text(text, length=limit)
                chunks = [[chunk] for chunk in chunks_]
                liste += chunks
                ids += [[identifier] for _ in chunks]
                logger.warning(f"The text contains {length_text} tokens, which exceeds the limit of {limit} tokens. It has been truncated to {len(text)} tokens. Please note that the `len()` function may not correctly count tokens for certain languages, such as Bulgarian. Therefore, you might encounter this warning even if the token count appears to be below the limit.")

            else :
                cpt += length_text
                if cpt < limit:
                    sub_list.append(text)
                    sub_ids.append(identifier)
                else :
                    liste.append(sub_list)
                    ids.append(sub_ids)
                    cpt, sub_list, sub_ids = length_text, [], []
                    sub_list.append(text)
                    sub_ids.append(identifier)

        if len(sub_list) !=0 :
            liste.append(sub_list)
            ids.append(sub_ids)
        
        if len(liste) != len(ids):
            raise ValueError(f"len(liste) = {len(liste)} and len(ids) = {len(ids)})")
        logger.info(f"Texts successfully split into sub-lists. len(liste) = {len(liste)} and len(ids) = {len(ids)})")
        return liste, ids

    def translate_liste(self,params: dict, list_of_text: list[str]): 
        
        """
        Translates a list of texts using an external translation API. The function sends 
        the list of texts to the API and handles the response, including character limit errors.

        Args:
            params (dict): The parameters required for the translation API, including source language, target language, and other settings.
            list_of_text (list[str]): A list of texts to be translated.

        Returns:
            list[str]: A list of translated texts if the request is successful. In case of an error, the function logs and prints the error details.
        """
        
        params['q'] = list_of_text
        response = requests.post(self.__base_url, params=params)

        if response.status_code == 411:
            logger.error("Error occur with language code ={params['source']}. Texts were not translated successfully. The number of characters exceeded the translation limit. Please inspect the portion of the text you are trying to translate and specify the correct character limit. The limit may vary depending on the language code.")
            
        elif response.status_code == 200:
            response = response.json()
            
            html_decoded = [self.html_decoder(item['translatedText']) for item in response['data']['translations']]
      
        else :
            logger.error(f"Unknown error with status code = {response.status_code }")
            
        return html_decoded
        
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
            html_decoded = self.translate_liste(list_of_text = list_of_text, params = params)
            responses.append(html_decoded)
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
        news_dataframe = news_dataframe.copy()
        news_dataframe.loc[:, 'translated_title'] = news_dataframe['titles'].values
        news_dataframe.loc[:,'translated_text'] = news_dataframe['texts'].values
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
            logger.info(f"language_limits[lang] = {language_limits[lang]}")

            ## Translating title
#             sub1, ids_title = self.split_liste(list(data_['titles']), limit=limit)
            texts, ids= self.split_liste(list(data_['titles']), limit=limit)
            texts = self.__translate_text(texts, source_language_code=lang)
            new_ids, news_texts = self.group_list(ids= ids, texts=texts)
            ids_, texts_ = self.contenate_list(ids= new_ids, texts = news_texts)
            final_texts, _ =  self.reorder_texts(ids=ids_, texts = texts_)
            data_['translated_title'] = final_texts
            print("*"*40)
            print("*"*40)
            print(f"language_limits[lang] = {language_limits[lang]}")
            print(f"lang = {lang}")
            print("*"*40)
            print("*"*40)

            ## Translating text
            texts, ids = self.split_liste(list(data_['texts']), limit=limit)
            texts = self.__translate_text(texts, source_language_code=lang)
            new_ids, news_texts = self.group_list(ids= ids, texts=texts)
            ids_, texts_ = self.contenate_list(ids= new_ids, texts = news_texts)
            final_texts, _ =  self.reorder_texts(ids=ids_, texts = texts_)
            data_['translated_text'] = final_texts

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
    
    
