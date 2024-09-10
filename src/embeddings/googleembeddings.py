import logging


import numpy as np
import pandas as pd
from google.cloud.exceptions import NotFound

from typing import Optional

from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
import sys
import os
sys.path.append("/home/jupyter/news/src")

from utils import create_logger, split_liste

logger = create_logger(__name__, 'google_embeddings.log')


class GoogleEmbeddings :
    """
    A class to create and handle embeddings using Google Vertex AI.

    Attributes
    ----------
    __embeddings (TextEmbeddingModel) : The embeddings model.
    __embedded_data (np.ndarray) : The embedded data from the dataframe.
    __task (str) :The task type for embeddings.
    __dimensionality (int) :The dimensionality of the embeddings.

    Methods
    -------
    __init__(vertexai_embedding_name: str = 'text-embedding-004', task: str = "CLUSTERING", dimensionality: Optional[int] = 256)
        Initializes the GoogleEmbeddings class with a specified Vertex AI embeddings model.
        
    __create_embeddings_models(vertexai_embedding_name: str) -> TextEmbeddingModel : 
        Creates an embeddings model from the given Vertex AI model name.
        
    embed_text(texts: list[str]) -> list[list[float]] :
        Embeds texts with a pre-trained, foundational model.
        
    fit_transform(dataframe: pd.DataFrame, col: str = 'translated_text', limit: int = 20000, separators: list[str] = ['.', '!', '?', '\n', '\n\n']) :
        Embeds the text in a specified column of a dataframe.
        
    embedded_data -> np.ndarray :
        Returns the embedded data from the dataframe.
        
    embeddings -> TextEmbeddingModel :
        Gets or sets the embeddings model.
    """
    
    def __init__(self, vertexai_embedding_name: str = 'text-embedding-004', task: str = "CLUSTERING", dimensionality: Optional[int] = 256) :
        """
        Initializes the GoogleEmbeddings class with a specified Vertex AI embeddings model.

        Args:
            vertexai_embedding_name (str): The name of the Vertex AI embeddings model. Defaults to 'text-embedding-004'.
            task (str): The task type for embeddings. Defaults to 'CLUSTERING'.
            dimensionality (int, optional): The dimensionality of the embeddings. Defaults to 256.
        """
        
        self.__task = task
        self.__dimensionality = dimensionality
        self.__embeddings = self.__create_embeddings_models(vertexai_embedding_name)
        self.__embedded_data : np.ndarry = None
        logger.info(f"Initialized GoogleEmbeddings with model: {vertexai_embedding_name}")
    
    
    def __create_embeddings_models(self, vertexai_embedding_name : str) -> TextEmbeddingModel:
        """
        Creates an embeddings model from the given Vertex AI model name.

        Args:
            vertexai_embedding_name (str): The name of the Vertex AI embeddings model.

        Returns:
            TextEmbeddingModel: The created embeddings model.

        Raises:
            NotFound: If the specified model is not found.
            Exception: For any other exceptions that occur.
        """
        try :
            model = TextEmbeddingModel.from_pretrained(vertexai_embedding_name)
            logger.info(f"Successfully created embeddings model: {vertexai_embedding_name}")
            return model
        
        except NotFound as e :
            error_message = ("Model not found. You can find the correct name here: 'https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings'")
            logger.error(f"NotFound: {vertexai_embedding_name}. {error_message}")
            print(error_message)
        except Exception as e :
            raise e

    
    def embed_text(self,texts: list[str]) -> list[list[float]]:
        """
        Embeds texts with a pre-trained, foundational model.

        Args:
            texts (list[str]): The list of texts to embed.

        Returns:
            list[list[float]]: The embedded texts as lists of floats.
        """
        inputs = [TextEmbeddingInput(text, self.__task) for text in texts]
        kwargs = dict(output_dimensionality=self.__dimensionality) if self.__dimensionality else {}
        embeddings = self.__embeddings.get_embeddings(inputs, **kwargs)
        
        return [embedding.values for embedding in embeddings]
    
    def fit_transform(self, sentences : list[str], limit = 20000, separators: list[str] = ['.', '!', '?', '\n', '\n\n']) :
        """
        Embeds the text in a specified column of a dataframe.

        Args:
            dataframe (pd.DataFrame): The dataframe containing the text to be embedded.
            col (str): The column name containing the text. Defaults to 'translated_text'.
            limit (int): The token limit for splitting texts. Defaults to 20000.
            separators (list[str]): The list of separators to use for splitting texts. Defaults to ['.', '!', '?', '\n', '\n\n'].

        Raises:
            ValueError: If the column does not exist in the dataframe.
        """
        list_of_texts = split_liste(sentences,limit = limit, separators=separators)
        texts = np.empty((0, self.__dimensionality))
       
        long = sum([len(texts_) for texts_ in list_of_texts])
        print(long)
        for texts_ in list_of_texts :
            embeddings_ =  np.array(self.embed_text(texts_))
            texts = np.concatenate([texts, embeddings_])
            
        self.__embedded_data = texts
        print(len(texts))
        logger.info("Successfully embedded the dataframe")
    
   
    @property
    def embedded_data(self):
        return self.__embedded_data
    
    @property
    def embeddings(self) -> TextEmbeddingModel:
        return self.__embeddings
    
    @embeddings.setter
    def embeddings(self, vertexai_embedding_name : str, task: str = "CLUSTERING", dimensionality: Optional[int] = 256):
        self.__embeddings = self.__create_embeddings_models(vertexai_embedding_name = vertexai_embedding_name, task = task, dimensionality = dimensionality)
        