import logging
from media.src.utils.utils import create_logger

# Configure the module-level logger
logger = create_logger()


from deep_translator import GoogleTranslator
from copy import deepcopy
from typing import Tuple
import numpy as np
import pandas as pd

from deep_translator.exceptions import RequestError

logger = create_logger(__name__, 'deepLtranslator.log')

class DeepLTranslation:
    """
    A class for handling text translation tasks using the GoogleTranslator.

    Attributes
    ----------
    translator : GoogleTranslator
        The translator object used for translating text. Defaults to translating from any language to English.

    Methods
    -------
    __init__():
        Initializes the DeepLTranslation class with a default translator if none is provided.

    __split_text(text, chunk_size):
        Splits a given text into smaller chunks based on the specified chunk_size, ensuring chunks end at a sentence boundary.

    __translate_prerpocesssing(texts: list[str], chunk_size: int) -> Tuple[list[int], list[str]]:
        Prepares text for translation by splitting it into chunks and generating corresponding IDs.

    __translate_prostprocessing(ids: list[int], chunks: list[str]) -> list[str]:
        Reconstructs the original text from translated chunks using the provided IDs.

    translation(dataframe: pd.DataFrame) -> pd.DataFrame:
        Translates the 'title' and 'text' columns of a given DataFrame from non-English languages to English.
    """
    
    def __init__(self) :
        """
        Initializes the DeepLTranslation class with a default translator.

        The default translator is set to translate from any language to English.
        """
        self.__translator = GoogleTranslator(source= "auto",target="english")
        logger.info("DeepLTranslation initialized with default translator.")
    
    def __split_text(self,text, chunk_size):
        """
        Splits a given text into smaller chunks based on the specified chunk_size, ensuring chunks end at a sentence boundary.

        Args:
            text(str) : The text to be split.
            chunk_size(int) : The maximum chunk_size of each chunk.

        Returns :
            list[str] :A list of text chunks.
        """
        
        if not isinstance(text, str):
            logger.error("Invalid text provided; must be a string.")
            raise ValueError("text must be a string")
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            logger.error("Invalid chunk_size provided; must be a positive integer.")
            raise ValueError("chunk_size must be a positive integer")
            
        # logger.info(f"Splitting text into chunks of size {chunk_size}.")
        sous_chaines = []
        
        while len(text) > chunk_size:
            pos = chunk_size
            while pos > 0 and text[pos] not in '.!?\n':
                pos -= 1
            pos += 1 #One include the ponctuation sign within the sub-string
            sous_chaines.append(text[:pos])
            text = text[pos:]
        sous_chaines.append(text)
        # logger.info("Text successfully split into chunks.")
        return sous_chaines

    def __translate_prerpocesssing(self,texts : list[str], chunk_size : int) -> Tuple[list[int], list[str]]:
        """
        Prepares text for translation by splitting it into chunks and generating corresponding IDs.

        Args:
            texts (list[str]): The list of texts to be translated.
            chunk_size (int): The maximum chunk_size of each chunk.

        Returns:
            tuple[list[int], list[str]]: A tuple containing a list of IDs and a list of text chunks.
        """
        
        if not all(isinstance(text, str) for text in texts):
            logger.error("Invalid texts provided; all elements in texts must be strings.")
            raise ValueError("All elements in texts must be strings")
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            logger.error("Invalid chunk_size provided; must be a positive integer.")
            raise ValueError("chunk_size must be a positive integer")
        
        logger.info("Preprocessing texts for translation.")
        chunks = []
        ids =[]
        for index,text in enumerate(texts):
            liste = self.__split_text(text, chunk_size)
            chunks += liste
            ids += [index] * len(liste)
        
        if len(chunks) != len(ids) :
            logger.error(f"Mismatch between the number of ids and chunks. len(chunks) = {len(chunks)} != len(ids) = {len(ids)}")
            raise ValueError(f"Mismatch between the number of ids and chunks. len(chunks) = {len(chunks)} != len(ids) = {len(ids)}")
        
        logger.info("Texts successfully preprocessed.")
        return ids, chunks
    
    def __translate_prostprocessing(self,ids : list[int], chunks : list[str]) -> list[str] :
        """
        Reconstructs the original text from translated chunks using the provided IDs.

        Args:
            ids (list[int]): The list of IDs corresponding to the chunks.
            chunks (list[str]): The list of translated text chunks.

        Returns:
            list[str]: A list of reconstructed texts.
        """

        if len(ids) != len(chunks) :
            logger.error(f"Mismatch between the number of ids and chunks. len(chunks) = {len(chunks)} != len(ids) = {len(ids)}")
            raise ValueError(f"Mismatch between the number of ids and chunks. len(chunks) = {len(chunks)} != len(ids) = {len(ids)}")
        
        if not all(isinstance(chunk, str) for chunk in chunks):
            logger.error("Invalid chunks provided; all elements in chunks must be strings.")
            raise ValueError("All elements in chunks must be strings")
        
        logger.info("Postprocessing translated chunks.")
        texts = []
        unique_id = np.unique(ids)
        id_array = np.array(ids)
        current = 0
        for ide in unique_id:
            chunk_id=np.where(id_array ==ide)[0]
            text=" ".join([chunks[i] for i in chunk_id])
            texts.append(text)

        logger.info("Chunks successfully postprocessed into original texts.")
        return texts

    def translation(self,dataframe : pd.DataFrame, chunk_size: int = 3000) -> pd.DataFrame:
        """
        Translates the 'title' and 'text' columns of a given DataFrame from non-English languages to English.

        Args:
            dataframe : pd.DataFrame
                The DataFrame containing text to be translated.

        Returns:
            pd.DataFrame
                The DataFrame with translated text.
        """
        
        required_columns = {'title', 'text', 'lang'}

        # Check if the DataFrame contains the required columns
        if not required_columns.issubset(dataframe.columns):
            missing_columns = required_columns - set(dataframe.columns)
            logger.error(f"The DataFrame is missing the following required columns: {', '.join(missing_columns)}")
            raise ValueError(f"The DataFrame is missing the following required columns: {', '.join(missing_columns)}")
        
        logger.info("Starting translation of DataFrame.")
        dataframe = dataframe.copy(deep= True)
        dataframe['translated_title'] = dataframe['title']
        dataframe['translated_text'] = dataframe['text']
        
        
        data_to_trans = dataframe.loc[dataframe['lang'] != "en", :]
        dataframe = dataframe.loc[dataframe['lang'] == "en", :]

        titles = list(data_to_trans['translated_title'])
        
        try:
            data_to_trans['translated_title'] = self.__translator.translate_batch(titles)
            logger.info("Titles successfully translated.")
        except Exception as e:
            logger.error(f"Error during title translation: {e}")
            raise ValueError(f"Error during title translation: {e}")

        texts = list(data_to_trans['translated_text'])
        
        ids, chunks = self.__translate_prerpocesssing(texts, chunk_size=chunk_size)
        
        try:
            chunks = self.__translator.translate_batch(chunks)
            logger.info("Text successfully translated.")
        except RequestError as e :
            logger.error(f"Error during title translation: {e}. Verifiy your connection or try new chunk_size lower than the current one : currenct chunk_size = {chunk_size}")
            raise ValueError(f"Error during title translation: {e}. Verifiy your connection or try new chunk_size lower than the current one : currenct chunk_size = {chunk_size}")
        except Exception as e:
            logger.error(f"Error during title translation: {e}")
            raise ValueError(f"Error during title translation: {e}. Verifiy your connection or try new chunk_size lower than the current one : currenct chunk_size = {chunk_size}")
            
        texts = self.__translate_prostprocessing(ids, chunks)

        data_to_trans['translated_text'] = texts
        
        self.dataframe = deepcopy(data_to_trans.reset_index(drop=True))
        
        logger.info("DataFrame translation completed.")
        return self.dataframe
    
    @property
    def translator(self):
        """
        Gets the current translator instance.

        Returns:
            GoogleTranslator: The current translator instance.
        """
        return self.__translator
    
    @translator.setter
    def translator(self, translator) :
        """
        Sets a new translator instance.

        Args:
            translator (GoogleTranslator): The new translator to be set.

        Raises:
            ValueError: If the provided translator is not an instance of GoogleTranslator.
        """
        if not isinstance(translator, GoogleTranslator) :
            logger.error("Invalid translator provided; must be an instance of GoogleTranslator.")
            raise ValueError("translator must be a GoogleTranslator instance")
        self.__translator = translator
        logger.info("Translator set successfully.")