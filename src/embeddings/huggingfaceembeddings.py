import logging
import sys
import os

sys.path.append("/home/jupyter/news/src")
from utils import create_logger
logger = create_logger(__name__, "huggingface_embedding.log")

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


class HuggingFaceEmbeddings :
    """
    A class to create and handle embeddings using Hugging Face models.

    Attributes
    ----------
        __embeddings (SentenceTransformer): The embeddings model from Hugging Face.
        __multi_processing (bool): Flag indicating whether multi-processing is used.
        __embedded_data (np.ndarray): The embedded data from the dataframe.

    Methods
    -------
        __init__(hugging_face_embedding_name: str, multi_processing: bool): Initializes the HuggingFaceEmbeddings class.
        __create_embeddings_models(hugging_face_embedding_name: str): Creates an embeddings model using the given name.
        fit_transform(dataframe: pd.DataFrame, col: str): Embeds the text in a specified column of a dataframe.
        embedded_data(): Returns the embedded data from the dataframe.
        embeddings(): Gets or sets the embeddings model.
    """

    def __init__(self, hugging_face_embedding_name: str = 'Alibaba-NLP/gte-large-en-v1.5', multi_processing = False) :
        """
        Initializes the HuggingFaceEmbeddings class with a specified Hugging Face embeddings model.

        Args:
            hugging_face_embedding_name (str): The name of the Hugging Face embeddings model. Defaults to 'Alibaba-NLP/gte-large-en-v1.5'.
            multi_processing (bool): Whether to use multi-processing for encoding. Defaults to False.
        """
        
        self.__embeddings = self.__create_embeddings_models(hugging_face_embedding_name)
        self.__multi_processing : bool = multi_processing # Hugging face multi-processing
        self.__embedded_data : np.ndarry = None # The embedded data
        logger.info(f"Initialized HuggingFaceEmbeddings with model: {hugging_face_embedding_name}, multi-processing: {multi_processing}")
    
    def __create_embeddings_models(self, hugging_face_embedding_name: str) :
        """
        Creates an embeddings model from the given Hugging Face model name.

        Args:
            hugging_face_embedding_name (str): The name of the Hugging Face embeddings model.

        Returns:
            SentenceTransformer: The created embeddings model.

        Raises:
            OSError: If there is an issue accessing the model.
            Exception: For any other exceptions that occur.
        """
        try :
            model = SentenceTransformer(hugging_face_embedding_name, trust_remote_code=True)
            logger.info(f"Successfully created embeddings model: {hugging_face_embedding_name}")
            return model
        except OSError as oe:
            error_message = (f"OSError: {oe}. There was an issue accessing the model = '{hugging_face_embedding_name}'. "
                             "Ensure the model identifier is correct and you have necessary permissions."
                             "You can also find some models here : 'https://huggingface.co/models' or here 'https://huggingface.co/spaces/mteb/leaderboard'")
            logger.error(error_message)
            print(error_message)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise e
            
    def fit_transform(self, sentences: list[str]) -> None:
        """
        Embeds the text in a specified column of a dataframe.

        Args:
            dataframe (pd.DataFrame): The dataframe containing the text to be embedded.
        """    
        if self.__multi_processing: 
            logger.info("Starting multi-processing pool for encoding.")
            
            pool = self.__embeddings.start_multi_process_pool()
            texts = self.__embeddings.encode_multi_process(sentences= sentences, pool=pool)
            self.__embeddings.stop_multi_process_pool(pool)
            
            logger.info("Multi-processing pool stopped.")
            
        else :
            texts = [self.__embeddings.encode(sentences= text) for text in sentences]

        logger.info("Successfully embedded the dataframe.")
        self.__embedded_data = np.array(texts)
    
    @property
    def embedded_data(self) -> np.ndarray:
        return self.__embedded_data
    
    @property
    def embeddings(self):
        return self.__embeddings
    
    @embeddings.setter
    def embeddings(self, hugging_face_embedding_name : str):
        self.__embeddings = self.__create_embeddings_models(hugging_face_embedding_name)