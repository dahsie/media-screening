
# from media.src.prompts.summarization_prompts import refine_template, prompt_template
from media.src.prompts.summarization_prompts import refine_prompt, prompt

#from summarization_prompts import refine_template, prompt_template


from langchain_google_genai import GoogleGenerativeAI
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import DataFrameLoader
from langchain_text_splitters import TokenTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from datetime import datetime
import pandas as pd
from media.src.utils.utils import create_logger
import re


logger, logfile_path = create_logger(__name__, 'summarizer.log')

class Summarizer :

    """
    A class to generate text summaries using Google's Generative AI model with a customizable summarization chain.

    Attributes
    ----------
    __llm : GoogleGenerativeAI
        The language model used for generating summaries.
    __chain_type : str
        The type of summarization chain to use (e.g., 'refine').
    __max_output_tokens : int
        The maximum number of tokens allowed for the summary output.
    __refine_prompt : PromptTemplate
        The prompt template used for refining the summaries.
    __prompt : PromptTemplate
        The base prompt template used for generating summaries.
    __chain : object
        The summarization chain used to process the input documents.
    dataframe : pd.DataFrame
        The DataFrame containing text data to be summarized.

    Methods
    -------
    __init__(model_name='gemini-1.5-flash', chain_type='refine', max_output_tokens=100):
        Initializes the Summarizer class with the specified model, chain type, and token limit.

    create_chain():
        Creates and returns a summarization chain based on the initialized parameters.

    get_documents_from_dataframe(dataframe: pd.DataFrame, document: str='translated_text', chunk_size: int=1000, chunk_overlap: int=100):
        Splits the text in a specified DataFrame column into smaller chunks for processing.

    genearate_description(json_data: list[dict], dataframe: pd.DataFrame, max_output_tokens=100, col_to_summarize: str='translated_text', chunk_size=1000, chunk_overlap=100) -> list[dict]:
        Generates summaries for the specified JSON data, refining the text content from a DataFrame column.
    """

    def __init__(self,google_api_key: str, model_name = 'gemini-1.5-flash', chain_type : str= 'refine', max_output_tokens:int =100):
        """
        Initializes the Summarizer class.

        Args:
            google_api_key (str).
            model_name (str, optional): The name of the Google Generative AI model to use. Defaults to 'gemini-1.5-flash'.
            chain_type (str, optional): The type of summarization chain to use. Defaults to 'refine'.
            max_output_tokens (int, optional): The maximum number of tokens allowed for the summary. Defaults to 100.
        """
        self.__llm: GoogleGenerativeAI= GoogleGenerativeAI(model = model_name, temperature=0.0, google_api_key = google_api_key)
        self.__chain_type : str = chain_type
        self.__max_output_tokens = max_output_tokens
        self.__prompt = prompt
        self.__refine_prompt = refine_prompt
        self.__chain = self.create_chain()
        self.dataframe : pd.DataFrame = None
        self.logfile_path = logfile_path
        logger.info('Summarizer has been initialized successfully!')
        
    
    
    def create_chain(self):
        """
        Creates a summarization chain using the initialized language model and prompts.

        Returns:
            object: The created summarization chain.
        """
        chain = load_summarize_chain(llm=self.__llm, chain_type=self.__chain_type, question_prompt=self.__prompt,
        refine_prompt=self.__refine_prompt, return_intermediate_steps=True,input_key="input_documents", output_key="output_text")
        
        logger.info('chain created successfully !')
        return chain

    def get_documents_from_dataframe(self,dataframe: pd.DataFrame, document: str='translated_text', chunk_size: int=1000, chunk_overlap: int=100) :
        """
        Splits text data from a specified column in a DataFrame into smaller chunks for summarization.

        Args:
            dataframe (pd.DataFrame): The DataFrame containing the text data.
            document (str, optional): The name of the column containing the text to be summarized. Defaults to 'translated_text'.
            chunk_size (int, optional): The maximum size of each text chunk. Defaults to 1000.
            chunk_overlap (int, optional): The number of overlapping characters between chunks. Defaults to 100.

        Returns:
            list: A list of document chunks ready for summarization.
        """
        df_loader = DataFrameLoader(dataframe, page_content_column=document)
        df_document = df_loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        docs = text_splitter.split_documents(df_document)
        
        logger.info(f"Splitting text data from the column '{document}' of the input DataFrame into smaller chunks for summarization.")
        return docs
    
    
    def genearate_description(self, json_data: list[dict], dataframe: pd.DataFrame, max_output_tokens = 100, col_to_summarize: str = 'translated_text', chunk_size = 1000, chunk_overlap=100) -> list[dict]:
        """
        Generates and refines descriptions for each item in a JSON list using text data from a DataFrame.

        Args:
            json_data (list[dict]): A list of dictionaries containing the data to be summarized.
            dataframe (pd.DataFrame): The DataFrame containing the source text data.
            max_output_tokens (int, optional): The maximum number of tokens for the summary. Defaults to 100.
            col_to_summarize (str, optional): The column name in the DataFrame to summarize. Defaults to 'translated_text'.
            chunk_size (int, optional): The maximum size of each text chunk. Defaults to 1000.
            chunk_overlap (int, optional): The number of overlapping characters between chunks. Defaults to 100.

        Returns:
            list[dict]: The JSON list with the added or updated descriptions.
        """
        logger.info('Starting desciption generation!')
        
        for index, item in enumerate(json_data):
            urls = []
            if item['relevant'] == 'yes':
                print('yes')
                urls += item['sources']
                if 'sub_articles' in item.keys():
                    for sub in item['sub_articles']:
                        urls += sub['sources'] if len(sub) != 0 else []
                        
                df = dataframe.loc[dataframe['url'].isin(urls), :] 
                dates_ = list(df['date'])
                dates = [datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ") for date in dates_]
                most_recent_date = max(dates)
                docs = self.get_documents_from_dataframe(dataframe = df, document = col_to_summarize, chunk_size= chunk_size, chunk_overlap= chunk_overlap)

                # result = self.__chain.invoke(docs)
                # result = self.__chain.invoke({"input_documents": docs, "max_tokens": self.__max_output_tokens}, return_only_outputs=True)
                result = self.__chain.invoke({"input_documents": docs, "max_tokens": self.__max_output_tokens}, return_only_outputs=True)
                result = result['output_text']
                result = re.sub(r'[#$].*?:|\*|\n|#', '', result)

                json_data[index]['description'] = result
                json_data[index]['date'] = most_recent_date.strftime("%Y-%m-%d")
                json_data[index]['sources'] = list(set(urls))
        
        logger.info('Description generated successfully!')
        return json_data

    # ------------------------------- PROPERTIES --------------------------------------------------------------------------

    @property
    def chain_type(self) -> None:
        return self.__chain_type

    @chain_type.setter
    def chain_type(chaine_type: str)-> None:
        self.__chain_type = chaine_type

    @property
    def llm(self)-> GoogleGenerativeAI:
        return self.__llm

    @property
    def chain(self):
        return self.__chain
    
    @property
    def prompt(self) -> PromptTemplate :
        return self.__prompt
    
    @property
    def refine_prompt(self) -> PromptTemplate :
        return self.__refine_prompt