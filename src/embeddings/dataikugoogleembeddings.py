import sys
import os
import numpy as np
import pandas as pd
from media.src.utils.utils import create_logger, split_liste


from typing import Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings


logger = create_logger(__name__, 'dataiku_google_embeddings.log')


class DataikuGoogleEmbeddings:

    """
    A class to create and handle text embeddings using Google Vertex AI.

    Attributes
    ----------
    __embeddings : GoogleGenerativeAIEmbeddings
        The embeddings model instance used for generating embeddings.
    __embedded_data : np.ndarray
        The array containing embedded data generated from the input text.
    __task : str
        The task type for which the embeddings are used (e.g., "CLUSTERING").
    __dimensionality : int
        The dimensionality of the generated embeddings.

    Methods
    -------
    __init__(vertexai_embedding_name: str = 'models/text-embedding-004', task: str = "CLUSTERING", dimensionality: Optional[int] = 768):
        Initializes the DataikuGoogleEmbeddings class with a specified Vertex AI embeddings model, task type, and dimensionality.

    __create_embeddings_models(vertexai_embedding_name: str) -> GoogleGenerativeAIEmbeddings:
        Creates and returns an embeddings model based on the given Vertex AI model name.

    fit_transform(sentences: list[str], limit: int = 20000, separators: list[str] = ['.', '!', '?', '\n', '\n\n']):
        Generates embeddings for a list of sentences, handling text splitting based on token limits and separators.
    """
    
    def __init__(self, google_api_key: str, vertexai_embedding_name: str = "models/text-embedding-004", task: str = "CLUSTERING", dimensionality: Optional[int] = 768):
        """
        Initializes the DataikuGoogleEmbeddings class with a specified Vertex AI embeddings model.

        Args:
            google_api_key(str) : The google api key.
            vertexai_embedding_name (str): The name of the Vertex AI embeddings model. Defaults to 'models/text-embedding-004'.
            task (str): The task type for which the embeddings will be used. Defaults to 'CLUSTERING'.
            dimensionality (int, optional): The dimensionality of the generated embeddings. Defaults to 768.
        """
        self.__task = task
        self.__dimensionality = dimensionality
        self.__embeddings = self.__create_embeddings_models(vertexai_embedding_name=vertexai_embedding_name, google_api_key=google_api_key)
        self.__embedded_data: np.ndarray = None
        logger.info(f"Initialized GoogleEmbeddings with model: {vertexai_embedding_name}")
    
    def __create_embeddings_models(self, vertexai_embedding_name: str, google_api_key: str) -> GoogleGenerativeAIEmbeddings:
        """
        Creates and returns an embeddings model based on the given Vertex AI model name.

        Args:
           .
            vertexai_embedding_name (str): The name of the Vertex AI embeddings model.

        Returns:
            GoogleGenerativeAIEmbeddings: The instantiated embeddings model.

        Raises:
            NotFound: If the specified model is not found.
            Exception: For any other exceptions that occur during model creation.
        """
        try:
            model = GoogleGenerativeAIEmbeddings(model=vertexai_embedding_name, task_type=self.__task, google_api_key=google_api_key)
            logger.info(f"Successfully created embeddings model: {vertexai_embedding_name}")
            return model
        except NotFound as e:
            error_message = ("Model not found. You can find the correct name here: 'https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings'")
            logger.error(f"NotFound: {vertexai_embedding_name}. {error_message}")
            print(error_message)
        except Exception as e:
            raise e

    def fit_transform(self, sentences: list[str], limit: int = 20000, separators: list[str] = ['.', '!', '?', '\n', '\n\n']):
        """
        Generates embeddings for a list of sentences, handling text splitting based on token limits and separators.

        Args:
            sentences (list[str]): The list of sentences to embed.
            limit (int, optional): The token limit for splitting texts. Defaults to 20000.
            separators (list[str], optional): The list of separators to use for splitting texts. Defaults to ['.', '!', '?', '\n', '\n\n'].

        Raises:
            ValueError: If the text cannot be embedded or if the input is invalid.
        """
        list_of_texts = split_liste(sentences, limit=limit, separators=separators)
        texts = np.empty((0, self.__dimensionality))
       
        long = sum([len(texts_) for texts_ in list_of_texts])
        print(long)
        for texts_ in list_of_texts:
            embeddings_ = np.array(self.__embeddings.embed_documents(texts_))
            texts = np.concatenate([texts, embeddings_])
            
        self.__embedded_data = texts
        logger.info("Successfully embedded the sentences.")
    

    # ------------------------------------ PROPERTIES ------------------------------------------------------------------------------

    @property
    def embedded_data(self):
        """
        Returns the embedded data generated from the input text.

        Returns:
            np.ndarray: The embedded data.
        """
        return self.__embedded_data
    
    @property
    def embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """
        Gets the current embeddings model.

        Returns:
            GoogleGenerativeAIEmbeddings: The current embeddings model.
        """
        return self.__embeddings
    
    @embeddings.setter
    def embeddings(self, google_api_key: str, vertexai_embedding_name: str, task: str = "CLUSTERING"):
        """
        Sets a new embeddings model based on the provided Vertex AI model name and task type.

        Args:
            google_api_key(str)
            vertexai_embedding_name (str): The name of the new Vertex AI embeddings model.
            task (str, optional): The task type for the new embeddings model. Defaults to "CLUSTERING".
        """
        self.__embeddings = self.__create_embeddings_models(vertexai_embedding_name=vertexai_embedding_name, task=task, google_api_key=google_api_key)

  
