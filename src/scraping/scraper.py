

from datetime import datetime, timedelta, date
import json
from abc import ABC, abstractmethod

import logging

import pandas as pd
from pandas import DataFrame





class Scraper(ABC):
    """
    After the data collection, the dataframe gathering the collected data can be cleaned. But this cleaning empty some dataframe that contain chinese of japanese data.
    """
    URLS =[]
    def __init__(self, country : str, lang : str, query=None, save_path: str = None,
                 end_date : str = date.today().strftime('%Y-%m-%d'),
                 ecart : int =1, start_date : str = None, timeout :float = 5,
                 user_agent : str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
                ):
        self.save_path = save_path
        self.news_are_collected :bool = False
        self.articles_dataframe : pd.DataFrame = None
        self.articles_json : dict = None
        self.end_date = end_date
        self.ecart = ecart
        self.start_date = start_date if start_date is not None else (datetime.strptime(end_date, '%Y-%m-%d').date() - timedelta(days=self.ecart)).strftime('%Y-%m-%d')
        # self.domain_manager = DomainManager()
        self.dataframe_is_cleaned = False
        self._query = query
        self.headers = user_agent
        logging.basicConfig(filename='./scraper.log', level=logging.INFO, format='%(asctime)s %(message)s')
        self._country = country
        self._lang = lang
        self._timeout = timeout
        
    @property
    def country(self):
        """
        Gets the country code for news collection.

        Returns:
            str: The country code.
        """
        return self._country

    @country.setter
    def country(self, country):
        """
        Sets the country code for news collection.

        Args:
            country (str): The country code.
        Raises:
            ValueError: If the country code is not a 2-character alphabetical string.
        """
        if not isinstance(country, str):
            raise ValueError("Country must be a string")
        if len(country)!= 2:
            raise ValueError("Country code must be 2 characters long")
        if not country.isalpha():
            raise ValueError("Country code must be alphabetical")
        self._country = country.upper()  # Normalize to uppercase

    @property
    def lang(self) :
        """
        Gets the language code for news collection.

        Returns:
            str: The language code.
        """
        return self._lang

    @lang.setter
    def lang(self, lang):
        """
        Sets the language code for news collection.

        Args:
            lang (str): The language code.
        Raises:
            ValueError: If the language code is not a 2-character alphabetical string.
        """
        if not isinstance(lang, str):
            raise ValueError("Language must be a string")
        if len(lang)!= 2:
            raise ValueError("Language code must be 2 characters long")
        if not lang.isalpha():
            raise ValueError("Language code must be alphabetical")
        self._lang = lang.lower()  # Normalize to lowercase

    @property
    def timeout(self) :
        """
        Gets the timeout value for web requests.

        Returns:
            float: The timeout value.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, timeout):
        """
        Sets the timeout value for web requests.

        Args:
            timeout (float): The timeout value.

        Raises:
            ValueError: If the timeout is not a positive float.
        """
        if not isinstance(timeout, float):
            raise ValueError('timeout should be a float')
        if timeout <=0 :
            raise ValueError('timeout should be none negative')
        self._timemout = timeout

    @property
    def query(self):
        """
        Gets the search query for news articles.

        Returns:
            str: The search query.
        """
        return self._query

    @query.setter
    def query(self, query) :
        """
        Sets the search query for news articles.

        Args:
            query (str): The search query.
        Raises:
            ValueError: If the query is not a non-empty string.
        """
        if not isinstance(query, str):
            raise ValueError("Query must be a string!")
        if len(query) <= 0 :
            raise ValueError("Query must not be empty")
        self._query = query


    def save_news(self, path_to_save : str ) :
        """
        Saves the collected news articles to a CSV file.

        Args:
            path_to_save (str): The path where the CSV file will be saved.

        Raises:
            ValueError: If news articles have not been collected yet.
        
        Note:
            Before calling this method, ensure that news articles have been collected by calling the `scrape` method.
        """
        
        if self.news_are_collected :
            self.articles_dataframe.to_csv(path_to_save, index=False)
        else :
            raise ValueError(f"News are not yet collected because  self.news_are_collected = {self.news_are_collected}! collect them before saving")
    
    

    def postprocess(self):
        """
        Cleans the articles DataFrame if it has not been cleaned.
        
        Note:
            This method calls `clean_dataframe` to clean the DataFrame. Ensure that `clean_dataframe` is implemented.
        """
        if self.dataframe_is_cleaned == False :
            clean_dataframe(self.articles_dataframe)
       
    def print_json(self) :
        """
        Prints the JSON representation of the collected articles.

        Note:
            The JSON data is pretty-printed with indentation for readability.
        """
        data = json.loads(self.articles_json)
        print(json.dumps(data, indent=4, sort_keys=False))
    
    
    @abstractmethod
    def search(self):
        pass
    
    @abstractmethod
    def process_article(self, *params):
        pass
    
    @abstractmethod
    def fetch_articles(self):
        pass
    
    @abstractmethod
    def scrapping(self, *params):
        pass
    
    def news_collection(self, news):
        """
        This method collects news articles from multiple sources.
        If the articles have not been collected yet, it builds the news sources and then either downloads and processes the articles in parallel (if `self.multi_threading` is True) or sequentially (if `self.multi_threading` is False).
        After the articles have been processed, they are stored in a DataFrame `self.articles` and the flag `self.news_are_collected` is set to True.
        If a save path `self.save_path` is provided, the articles are also saved to a CSV file at that location.

        Note:
            This method logs the start and end of the building, downloading, processing, and saving processes. Make sure to set up logging before calling this method.
        """
        
        self.articles_dataframe = pd.DataFrame(news)
        
        print("News collection ended ! ")
        self.news_are_collected = True 
        if self.save_path is not None :
            self.save_news(self.save_path)
            logging.info(f'Saved articles to {self.save_path}')
        if self.articles_dataframe is not None :
            self.articles_json = self.articles_dataframe.to_json(orient='records')
            self.articles_dataframe['lang'] = self._lang
            self.articles_dataframe['cat']= self._query
            
