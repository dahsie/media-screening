import logging


# Configure the module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler
file_handler = logging.FileHandler('google_embeddings.log')
file_handler.setLevel(logging.INFO)

# Create a formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s [%(levelname)s] -- [%(funcName)s()] : %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)


import numpy as np
import pandas as pd
from google.cloud.exceptions import NotFound
from langchain_google_vertexai import VertexAIEmbeddings


class GoogleEmbeddings :
    
    """
    A class to create and handle embeddings using Google Vertex AI.

    Attributes
    ----------
        __embeddings (VertexAIEmbeddings): The embeddings model.
        __embedded_data (np.ndarray): The embedded data from the dataframe.
        __dataframe (pd.DataFrame): The dataframe with embedded data.

    Methods
    -------
        __init__(vertexai_embedding_name: str): Initializes the GoogleEmbeddings class.
        __create_embeddings_models(vertexai_embedding_name: str): Creates an embeddings model.
        fit_tansform(dataframe: pd.DataFrame, col: str): Embeds the text in a specified column of a dataframe.
        embedded_data(): Returns the embedded data from the dataframe.
        embeddings(): Gets or sets the embeddings model.
    """
    def __init__(self, vertexai_embedding_name: str = 'textembedding-gecko@003') :
        """
        Initializes the GoogleEmbeddings class with a specified Vertex AI embeddings model.

        Args:
            vertexai_embedding_name (str): The name of the Vertex AI embeddings model. Defaults to 'textembedding-gecko@003'.
        """
        
        self.__embeddings = self.__create_embeddings_models(vertexai_embedding_name)
        self.__embedded_data : np.ndarry = None
        self.__dataframe : pd.DataFrame = None
        logger.info(f"Initialized GoogleEmbeddings with model: {vertexai_embedding_name}")
    
    
    def __create_embeddings_models(self, vertexai_embedding_name : str) :
        """
        Creates an embeddings model from the given Vertex AI model name.

        Args:
            vertexai_embedding_name (str): The name of the Vertex AI embeddings model.

        Returns:
            VertexAIEmbeddings: The created embeddings model.

        Raises:
            NotFound: If the specified model is not found.
            Exception: For any other exceptions that occur.
        """
        try :
            
            model = VertexAIEmbeddings(model_name= vertexai_embedding_name)
            logger.info(f"Successfully created embeddings model: {vertexai_embedding_name}")
            return model
        
        except NotFound as e :
            error_message = ("Model not found. You can find the correct name here: 'https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings'")
            logger.error(f"NotFound: {vertexai_embedding_name}. {error_message}")
            print(error_message)
        except Exception as e :
            raise e
            
    def fit_transform(self, dataframe :pd.DataFrame, col: str = 'translated_text') :
        """
        Embeds the text in a specified column of a dataframe.

        Args:
            dataframe (pd.DataFrame): The dataframe containing the text to be embedded.
            col (str): The column name containing the text. Defaults to 'translated_text'.
        """
        
        dataframe = dataframe.copy(deep=True)
        logger.info(f"Embedding dataframe with column: {col}")
        
        dataframe.loc[:, col] = dataframe[col].str.replace('\n', ' ')
       
        dataframe.loc[:, 'embedding'] = dataframe[col].apply(lambda x : np.array(self.embeddings.embed_query(x)))
            
        self.__embedded_data, self.__dataframe  = np.vstack(dataframe['embedding'].values), dataframe
        logger.info("Successfully embedded the dataframe")
    
    @property
    def dataframe(self):
        """
        Gets the dataframe with the embedding
        pd.DataFrame: The all dataframe with the embedding within. 
        """
        return self.__dataframe
    @property
    def embedded_data(self):
        """
        Gets the embedding data
        np.ndarray: The embedded data from the dataframe.
        """
        return self.__embedded_data
    
    @property
    def embeddings(self):
        """
        Gets the embedding models
        VertexAIEmbeddings: The embeddings model.
        """
        return self.__embeddings
    
    @embeddings.setter
    def embeddings(self, vertexai_embedding_name : str):
        """
        Sets a new embeddings model.

        Args:
            vertexai_embedding_name (str): The name of the new Vertex AI embeddings model.
        """
        try :
            self.__embeddings = VertexAIEmbeddings(model_name=vertexai_embedding_name)
            logger.info(f"Set new embeddings model: {vertexai_embedding_name}")
            
        except NotFound :
            error_message = ("Model not found. You can find the correct name here: 'https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings'")
            logger.error(f"NotFound: {vertexai_embedding_name}. {error_message}")
            print(error_message)
        except Exception as e :
            logger.error(f"Unkonown error :{e}")
            raise e
        