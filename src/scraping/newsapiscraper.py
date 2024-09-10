
from media.src.scraping.scraper import *

import requests
import re
import math
from newspaper import  Article

from tqdm import tqdm

#import sys
#sys.path.append("../src/utils")

#from utils import create_logger

from media.src.utils.utils import create_logger
logger = create_logger(__name__, 'news_api_scrapper.log')

class NewsApiScraper(Scraper) :
    """
    A scraper for fetching news articles from the NewsAPI.

    This class extends the Scraper class and provides functionality to fetch, process,
    and store news articles using the NewsAPI. It supports querying by topic, date ranges,
    and additional filters.

    Attributes
    ----------
        country (str) : The country code (e.g., 'us', 'fr') for news filtering.
        lang (str) : The language code (e.g., 'en', 'fr') for news filtering.
        query (str, optional) : A search query to filter the news articles.
        topic (str, optional) : A topic to filter the news articles (e.g., 'business', 'technology').
        save_path (str, optional) : Path to save the collected news articles as a CSV file.
        start_date (str, optional) : The start date for the news articles (format 'YYYY-MM-DD').
        end_date (str, optional) : The end date for the news articles (format 'YYYY-MM-DD').
        ecart (int) : The number of days to subtract from the end date to determine the start date if not provided.
        api_key (str) : API key for accessing the NewsAPI.
        timeout (float) : Timeout duration for HTTP requests.
        _url (str, optional) : The URL constructed for querying the NewsAPI.
        pages (int) : The number of pages required for pagination based on the total results.
        total_results (int) : The total number of results returned by the API.
        articles (dict) : Dictionary containing lists of collected article data.
        sources (list) : List of source names from which articles were collected.

    Methods
    -------
        __init__(api_key: str, country: str = "US", lang: str = "en", query: str = None,
                 topic: str = None, save_path: str = None, start_date: str = None,
                 end_date: str = date.today().strftime('%Y-%m-%d'), ecart: int = 1,
                 timeout: float = 5) -> None:
            Initializes the NewsApiScraper with the provided parameters.

        search() -> dict:
            Performs a search query on the NewsAPI based on the provided parameters.
            Constructs the URL for querying the NewsAPI based on the query, topic, and date range.
            Returns the JSON response from the API.

        set_params() -> None:
            Sets the parameters for pagination and total results based on the search response.
            Calls the `search` method to obtain the total number of results and calculates
            the number of pages required for fetching all the articles.

        process_article(article: dict, **kwargs) -> None:
            Processes an individual article and appends relevant information to the lists contained
            in the kwargs dictionary. Raises a ValueError if one or more required lists are missing.

        fetch_articles() -> None:
            Fetches and processes articles from the API across multiple pages.
            Uses pagination to collect all articles matching the search parameters.

        scrapping(**kwargs) -> dict:
            Downloads and extracts text content from the article links.
            Args:
                links (list): List of article URLs.
                dates (list): List of article publication dates.
                times (list): List of article publication times.
                descriptions (list): List of article descriptions.
                titles (list): List of article titles.
                verbose (bool, optional): If True, prints progress information. Default is False.
            Returns:
                dict: A dictionary containing the articles with their extracted text.

        news_collection() -> None:
            Collects news articles, processes them, and optionally saves them.
            Fetches articles, extracts relevant information, and uses the parent class's
            `news_collection` method to save the articles if a save path is provided.
        """
    
    def __init__(self, api_key :str,country :str ="US",lang : str="en",query :str = None,
                 topic :str = None,save_path : str = None,start_date :str= None, #year-moonth-day (i.e '2024-05-18')
                 end_date :date = date.today().strftime('%Y-%m-%d'),ecart : int =1,
                 timeout : float = 5
                ) -> None:
        """
        Initializes the NewsApiScraper with the provided parameters.

        Args:
            api_key (str): API key for accessing the NewsAPI.
            country (str): Country code for news filtering. Defaults to 'US'.
            lang (str): Language code for news filtering. Defaults to 'en'.
            query (str, optional): Search query for filtering news articles.
            topic (str, optional): Topic for filtering news articles.
            save_path (str, optional): Path to save collected news articles.
            start_date (str, optional): Start date for the news articles (format 'YYYY-MM-DD').
            end_date (str, optional): End date for the news articles (format 'YYYY-MM-DD').
            ecart (int): Number of days to subtract from the end date to determine the start date if not provided.
            timeout (float): Timeout duration for HTTP requests.
        """
        super(NewsApiScraper, self).__init__(save_path = save_path, end_date = end_date, ecart = ecart,
                        start_date = start_date, query = query, timeout = timeout,
                         country = country,lang = lang)
        self._api_key = api_key
        self._url = None

    def search(self) -> dict :
        """
        Performs a search query on the NewsAPI based on the provided parameters.

        Constructs the URL for querying the NewsAPI based on the query, topic, and date range.
        Returns the JSON response from the API.

        Returns:
            dict: A dictionary containing the search results from the NewsAPI.
        
        Raises:
            ValueError: If an invalid topic is provided or if neither query nor topic is provided.
        """
        if self.query is not None : #ser=arch by query
            query = self.query.split()
            query = "+".join(query)
            url = ('https://newsapi.org/v2/everything?'
                       f'q={query}&'
                       f'apiKey={self._api_key}')
            if self._lang is not None :
                url = url + f'&language={self._lang}'
            if self.start_date is not None and self.end_date is not None:
                url = url + (f'&from={self.start_date}&'
                       f'to={self.end_date}')
            self._url = url
            logger.info(f'Searching with query: {url}')
            return requests.get(url).json()

        elif self.topic is not None : # Search by topic
            try:
                url = ('https://newsapi.org/v2/top-headlines?'
                       f'country={self._country}&'
                       f'apiKey={self._api_key}&'
                       f'category={self.topic}')
                self._url= url
                logger.info(f'Searching with topic: {url}')
                return requests.get(url).json()
            except Exception as e:
                logger.error(f"Invalid topic provided. Accepted topics are : {'business,entertainment,general,health,science,sports,technology'}. more info about the error : {e}")
                
        else :
            url = ('https://newsapi.org/v2/top-headlines?'
                       f'country={self._country}&'
                       f'apiKey={self._api_key}')
            self._url = url
            logger.warning('No query or topic provided. Fetching top headlines.')
            return requests.get(url).json()
    

    def set_params(self) -> None :
        """
        Sets the parameters for pagination and total results based on the search response.

        Calls the `search` method to obtain the total number of results and calculates
        the number of pages required for fetching all the articles.

        Returns:
            None
        """
        response = self.search()
        self.pages = math.ceil(response['totalResults']/100) if 'totalResults' in response.keys() else 0
        self.total_results = response['totalResults'] if 'totalResults' in response.keys() else 0
        logger.info(f'Pagination set: {self.pages} pages, Total results: {self.total_results}')
    
    def process_article(self,article, **kwargs):
        """
        Processes an individual article and appends relevant information to the lists contained
        in the kwargs dictionary. Raises a ValueError if one or more required lists are missing.

        Args:
            article (dict): The article data obtained from the API.
            **kwargs: A dictionary containing lists to store article information:
                - 'links' (list): List to store article URLs.
                - 'dates' (list): List to store article publication dates.
                - 'titles' (list): List to store article titles.
                - 'descriptions' (list): List to store article descriptions.
                
        Raises:
            ValueError: If one or more required lists are missing from kwargs.
        """
        expected_keys = {'links', 'dates', 'titles', 'descriptions'}
        if not expected_keys.issubset(kwargs.keys()):
            logger.error("Missing one or more required lists in kwargs.")
            raise ValueError("Missing one or more required lists in kwargs")
        
        if article['url'] not in kwargs['links'] and article['url'] not in self.URLS:
            self.URLS.append(article['url'])
            kwargs['links'].append(article['url'])
            kwargs['descriptions'].append(article['description'])
            kwargs['titles'].append(article['title'])
            published_date = datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
            kwargs['dates'].append(published_date.strftime('%Y-%m-%dT%H:%M:%SZ'))

    def fetch_articles(self) -> None:
        """
        Fetches and processes articles from the API across multiple pages.

        Uses pagination to collect all articles matching the search parameters. Updates the lists
        of links, dates, titles, and descriptions with the processed data.

        Returns:
            None
        """
        
        sources = set()
        kwargs = {
            "dates" : [],
            "titles" : [],
            "descriptions" : [],
            "links" : []
        }

        self.set_params()
        
        for page in range(self.pages):
            url = self._url + f"page={page +1}"
            json_data = requests.get(url).json()
            
            for article in json_data['articles'] :
                sources.add(article['source']['name'])
                self.process_article(article=article, **kwargs)
                
        self.articles = kwargs
        self.sources = list(sources)
        print("search ended !")
            
    def scrapping(self, **kwargs):
        """
        Downloads and extracts text content from the article links.

        Args:
            **kwargs: A dictionary containing lists to store article information:
                -links (list): List of article URLs.
                -dates (list): List of article publication dates.
                -times (list): List of article publication times.
                -descriptions (list): List of article descriptions.
                -titles (list): List of article titles.

        Returns:
            dict: A dictionary containing the articles with their extracted text.
        """
        
        article = Article("//")
        texts = []
        for i, link in enumerate(tqdm(kwargs["links"])):

            text =''
            try :
                response = requests.get(link)

                if response.status_code ==200 :

                    article.download(input_html=response.content)
                    article.parse()
                    text = article.text

            except Exception as e :
                text = kwargs["descriptions"][i]
                logger.warning(f'Failed to download article from {link}')
                
            if text == '' :
                text = kwargs["descriptions"][i]
                
            texts.append(text)
        
        self.articles['texts']  = texts
        del self.articles["descriptions"]

    def news_collection(self):
        """
        Collects news articles, processes them, and optionally saves them.

        Fetches articles, extracts relevant information, and uses the parent class's
        `news_collection` method to save the articles if a save path is provided.

        Returns:
            None
        """
        self.fetch_articles()
        self.scrapping(**self.articles)
        super(NewsApiScraper, self).news_collection(self.articles)
        logger.info("News collection completed.")
        