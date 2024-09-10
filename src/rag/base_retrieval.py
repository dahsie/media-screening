
import json
from abc import ABC, abstractmethod

import pandas as pd
from pandas import DataFrame
import numpy as np

import logging
from typing import Tuple, Optional, List, Literal
from copy import deepcopy
from datetime import datetime, timedelta, date
from time import sleep, time
from tqdm import tqdm

# from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings, GoogleGenerativeAI
from langchain_community.document_loaders import DataFrameLoader
from langchain_core.output_parsers import  JsonOutputParser

from langchain_text_splitters import TokenTextSplitter, RecursiveCharacterTextSplitter

from langchain_community.vectorstores import FAISS

from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnableLambda
from langchain_core.documents import Document

class RetrivalBase(ABC):
    """
    Base class for retrieving and processing information from a DataFrame, with support for document embedding and query-based retrieval using Vertex AI and FAISS.
    
    ---------------------------------------------------------------------------------
    Attributes:
        liste (list[str]): A list of placeholder strings indicating missing or unknown data.
        core_name_prompt (PromptTemplate): A prompt template for extracting the core name of an organization from a complex title.
        embeddings (VertexAIEmbeddings): An instance of VertexAIEmbeddings for document embedding.
        llm (VertexAI): An instance of VertexAI for language model operations.
        core_chain (callable): A chain that processes the core name prompt through the language model.
        max_doc (int): The maximum number of documents to retrieve.
        chunk_size (int): The size of chunks for document splitting.
        chunk_overlap (int): The overlap between chunks for document splitting.
        failed_labels (list[int]): A list to keep track of failed labels during information retrieval.
        retry_number (int): The number of retry attempts for information retrieval.
        all_results (list[dict]): A list to store all results from the information retrieval process.
        results (list[dict]): A list to store the current batch of results.
        number_token (int): A counter for the number of tokens processed.
        pop_indices (list): A list of indices to be removed after postprocessing.

    --------------------------------------------------------------------------------
    Methods:
        __init__(self, vertexai_llm: str, vertexai_embedding_name: str, retry: int, max_doc: int, chunk_size: int, chunk_overlap: int):
            Initializes the RetrivalBase class with the given parameters and sets up embeddings and language model instances.
        
        _format_docs(self, docs: Document) -> str:
            Formats a list of documents into a single concatenated string.
        
        _get_documents_from_dataframe(self, dataframe: pd.DataFrame, chunk_size: int, chunk_overlap: int, document: str = 'translated_text') -> Document:
            Retrieves documents from a DataFrame, splits them into chunks, and returns the resulting list of documents.
        
        _create_db(self, docs) -> FAISS:
            Creates a FAISS database from the given documents.
        
        _retrieve(self, query: str) -> list[list, str, str]:
            Retrieves documents based on the given query and returns a list of sources, a summary of the document, and the concatenated document content.
        
        __postprocessing(self):
            Processes the retrieved results to handle missing or unknown values, and extracts the core company name.
        
        retrieve_infos_with_retry(self, dataframe: pd.DataFrame):
            Retrieves information from the DataFrame with retries for failed labels and processes the results.
    """
    
    core_name_prompt = PromptTemplate(
    template="""Given a complex corporate title, extract the fundamental or base name that truly represent the core identity of the organization. 
    Here is the organization : "{organization}". Keep in mind that the base name usually signifies the most prominent and defining component of the organization's identity
    Return only the extracted name.
    """
    ,
    input_variables=["organization"],
    )
    
    liste = ['n/a', 'unknown', 'not mentioned', 'none', 'null']
    
    def __init__(self, google_api_key: str, vertexai_llm: str, vertexai_embedding_name : str, retry :int, max_doc : int, chunk_size :int, chunk_overlap : int):
        """
        Initializes the RetrivalBase class with the given parameters and sets up embeddings and language model instances.
        
        Args:
            vertexai_llm (str): The model name for the Vertex AI language model.
            vertexai_embedding_name (str): The model name for the Vertex AI embeddings.
            retry (int): The number of retry attempts for information retrieval.
            max_doc (int): The maximum number of documents to retrieve.
            chunk_size (int): The size of chunks for document splitting.
            chunk_overlap (int): The overlap between chunks for document splitting.
        """
        
        # self.embeddings : VertexAIEmbeddings = VertexAIEmbeddings(model_name=vertexai_embedding_name) # CCP version
        self.embeddings : GoogleGenerativeAIEmbeddings = GoogleGenerativeAIEmbeddings(model=vertexai_embedding_name, google_api_key = google_api_key)
        
        # self.llm : VertexAI = VertexAI(model_name=vertexai_llm, temperature=0.0) #   GCP version
        self.llm :  GoogleGenerativeAI =  GoogleGenerativeAI(model=vertexai_llm, temperature=0.0, google_api_key = google_api_key)
        
        self.core_chain  = (self.core_name_prompt | self.llm)
        
        
        self.max_doc : int = max_doc
        self.chunk_size: int = chunk_size
        self.chunk_overlap: int = chunk_overlap
        
        self.failed_labels : list[int] = None
        self.retry_number : int = retry
        self.failed_labels : list[int] = []
        self.all_results : list[dict] = []
        self.results : list[dict] =[]
        self.number_token : int =0
        self.pop_indices: list = []
  
    
    def _format_docs(self,docs: Document) -> str:
        """
        Formats a list of documents into a single concatenated string.
        
        Args:
            docs (Document): A list of documents to format.
        
        Returns:
            str: The concatenated content of the documents.
        """
    
        return "\n\n".join(doc.page_content for doc in docs)
   
    def _get_documents_from_dataframe(self,dataframe : pd.DataFrame, chunk_size : int, chunk_overlap: int,  document: str='translated_text') -> Document :
        """
        Create langchain documents from a DataFrame.
        
        Args:
            dataframe (pd.DataFrame): The DataFrame containing the documents.
            chunk_size (int): The size of chunks for document splitting.
            chunk_overlap (int): The overlap between chunks for document splitting.
            document (str): The column name containing the document text. Default is 'translated_text'.
        
        Returns:
            Document: A list of documents after splitting.
        """
        df_loader = DataFrameLoader(dataframe, page_content_column=document)
        df_document = df_loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        docs = text_splitter.split_documents(df_document)
                                     
        return docs

    def _create_db(self,docs) :
        """
        Creates a FAISS database from the given documents.
        
        Args:
            docs: A list of documents to be added to the FAISS database.
        
        Returns:
            FAISS: The created FAISS database instance.
        """
        qdrant_db = FAISS.from_documents(docs, self.embeddings)
        return qdrant_db

    
    def _retrieve(self, query : str) -> list[list, str,str] :
        """
        Retrieves documents based on the given query and returns a list of sources, a summary of the document, and the concatenated document content.
        
        Args:
            query (str): The query for which a document must be retrieved.
        
        Returns:
            list: 
                - A list of hyperlinks showing where the retrieved document came from.
                - A list of published date for each retrieved document. 
                - The retrieved documents' page content concatenated.
        """
        docs  = self._retriever.invoke(query)
        
        if len(docs) != 0:
            sources = [docs[i].metadata['url'] for i in range(len(docs))]
            title = [docs[i].metadata['translated_title'] for i in range(len(docs))]
            published_date = list(set([docs[i].metadata['date'] for i in range(len(docs))]))
            title = " ".join(title)
            str_docs = title +"\n" + self._format_docs(docs)
            
            return sources, published_date,str_docs
        
        return None, None, None


    def __postprocessing(self) :
        """
        Processes the retrieved results to handle missing or unknown values, and extracts the core company name.
        """
        
        pop_index = []
        
        for index, item in enumerate(self.all_results):
            dict_instance = isinstance(item, dict)
            keys = item.keys()
            if not dict_instance:
                pop_index.append(index)
                continue
            if dict_instance and 'impacted_company' not in keys:
                pop_index.append(index)
                continue
            if dict_instance and 'impacted_business_sectors' not in keys :
                item['impacted_business_sectors'] = []
            try :
                
                if item['impacted_company'] is None or item['impacted_company'].lower() in self.liste:
                    item['impacted_company'] = ''
                    item['core_company'] = ''
                else :
                    core_name = self.core_chain.invoke(item['impacted_company']).strip()
                    item['core_company'] = core_name if len(core_name) !=0 else item['impacted_company']
                for location in item['locations'] :
                    if location['city'] is None or location['city'].lower() in liste:
                        location['city'] = ''
                    elif location['country'] is None or location['country'].lower() in self.liste:
                        location['country'] = ''
            except Exception as e :
                # print(item)
                pop_index.append(index)
        self.pop_index = pop_index
        
        
    def retrieve_infos_with_retry(self, dataframe : pd.DataFrame) :
        """
        Retrieves information from the DataFrame with retries for failed labels and processes the results.
        
        Args:
            dataframe (pd.DataFrame): The DataFrame from which to retrieve information.
        """
        self.retrieve_infos(dataframe)
        self.all_results += self.results
        
        retry = 0 
        
        while retry < self.retry_number and len(self.failed_labels) != 0 :
            retry+=1
            print('-------------------------------------------------------------------------------------')
            print(f"retying attempt {retry}")
            print(f"label len {len(self.failed_labels)}")
            print(f"labels {self.failed_labels}")
            dataframe = dataframe.loc[dataframe['class'].isin(self.failed_labels) , :].sort_values(by= 'class')
            self.retrieve_infos(dataframe)
            self.all_results += self.results
            
        self.__postprocessing()
        # self.all_results = [item for index, item in enumerate(self.all_results) if index not in self.pop_index]
        
        
    @abstractmethod
    def retrieve_infos(self, dataframe : pd.DataFrame) :
        pass