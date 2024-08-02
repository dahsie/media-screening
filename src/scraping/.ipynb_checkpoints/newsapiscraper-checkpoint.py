
from scraper import *


import requests
import re
import math

from newspaper import  Article, Config

from tqdm import tqdm


class NewsApiScraper(Scraper) :
    """
    A scraper for fetching news articles from the NewsAPI.

    This class extends the Scraper class and provides functionality to fetch, process,
    and store news articles using the NewsAPI. It supports querying by topic, date ranges,
    and additional filters.

    Attributes:
        country (str): The country code (e.g., 'us', 'fr') for news filtering.
        lang (str): The language code (e.g., 'en', 'fr') for news filtering.
        query (str, optional): A search query to filter the news articles.
        topic (str, optional): A topic to filter the news articles (e.g., 'business', 'technology').
        save_path (str, optional): Path to save the collected news articles as a CSV file.
        start_date (str, optional): The start date for the news articles (format 'YYYY-MM-DD').
        end_date (str, optional): The end date for the news articles (format 'YYYY-MM-DD').
        ecart (int): The number of days to subtract from the end date to determine the start date if not provided.
        api_key (str): API key for accessing the NewsAPI.
        timeout (float): Timeout duration for HTTP requests.
    """
    
    def __init__(self, api_key :str,country :str,lang : str,query :str = None,
                 topic :str = None,save_path : str = None,start_date :str= None, #year-moonth-day (i.e '2024-05-18')
                 end_date :date = date.today().strftime('%Y-%m-%d'),ecart : int =1,
                 timeout : float = 5
                ) -> None:
        
        super(NewsApiScraper, self).__init__(save_path = save_path, end_date = end_date, ecart = ecart,
                        start_date = start_date, query = query, timeout = timeout,
                         country = country,lang = lang)
        self._api_key = api_key
        self._url = None

    def search(self) -> dict :
        """
        Performs a search query on the NewsAPI based on the provided parameters.

        The search method constructs the appropriate URL for querying the NewsAPI based on the
        query, topic, and date range. It returns the JSON response from the API.

        Returns:
            dict: A dictionary containing the search results from the NewsAPI.
        
        Raises:
            Exception: If an invalid topic is provided.
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
            return requests.get(url).json()

        elif self.topic is not None : # Search by topic
            try:
                url = ('https://newsapi.org/v2/top-headlines?'
                       f'country={self._country}&'
                       f'apiKey={self._api_key}&'
                       f'category={self.topic}')
                self._url= url
                return requests.get(url).json()
            except Exception as e:
                print(f"Accepted topics are : {'business,entertainment,general,health,science,sports,technology'}")

        else :
            url = ('https://newsapi.org/v2/top-headlines?'
                       f'country={self._country}&'
                       f'apiKey={self._api_key}')
            self._url = url
            return requests.get(url).json()
    

    def set_params(self) :
        """
        Sets the parameters for pagination and total results based on the search response.

        This method calls the `search` method to obtain the total number of results and calculates
        the number of pages required for fetching all the articles.
        """
        response = self.search()
        self.pages = math.ceil(response['totalResults']/100)
        self.total_resulats = response['totalResults']
    
    def process_article(self,article, links, dates, times, descriptions, titles):
        """
        Processes an individual article and appends relevant information to the lists.

        Args:
            article (dict): The article data obtained from the API.
            links (list): List to store article URLs.
            dates (list): List to store article publication dates.
            times (list): List to store article publication times.
            descriptions (list): List to store article descriptions.
            titles (list): List to store article titles.
        """
        if article['url'] not in links and article['url'] not in self.URLS:
            self.URLS.append(article['url'])
            links.append(article['url'])
            descriptions.append(article['description'])
            titles.append(article['title'])
            published_date = datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
            
            dates.append(f"{published_date.year}-{published_date.month:02d}-{published_date.day:02d}")
            times.append( f"{published_date.hour:02d}:{published_date.minute:02d}:{published_date.second:02d}")

    def fetch_articles(self):
        """
        Fetches and processes articles from the API across multiple pages.

        This method uses pagination to collect all articles matching the search parameters. It
        updates the lists of links, dates, times, descriptions, and titles with the processed data.
        """
        
        sources = set()
        articles, dates, times, links, descriptions, titles = [],[],[],[], [], []

        self.set_params()
        
        for page in range(self.pages):
            url = self._url + f"page={page +1}"
            json_data = requests.get(url).json()
            
            for article in json_data['articles'] :
                sources.add(article['source']['name'])
                self.process_article(article=article, links=links, dates=dates, times=times, descriptions=descriptions, titles=titles)
                
        self.links, self.dates, self.times, self.descriptions,  self.titles = links, dates, times, descriptions, titles
        self.sources = list(sources)
        print("search ended !")
            
    def scrapping(self,links, dates, times, descriptions, titles, verbose = False):
        """
        Downloads and extracts text content from the article links.

        Args:
            links (list): List of article URLs.
            dates (list): List of article publication dates.
            times (list): List of article publication times.
            descriptions (list): List of article descriptions.
            titles (list): List of article titles.
            verbose (bool, optional): If True, prints progress information. Default is False.

        Returns:
            list: A list of dictionaries, each containing the article's date, time, title, URL, and text.
        """
        
        conf = Config()
        article = Article("//")
        papers = []
        conf.timeout, conf.fetch_images, conf.thread_timeout_seconds = self._timeout, False, 3
        for i, link in enumerate(tqdm(links)):

            text = ''
            data = {
                    "date" : dates[i],
                    "time" : times[i],
                    "title" : titles[i],
                    "url" : link,
                }
            try :
                response = requests.get(link)

                if response.status_code ==200 :

                    article.download(input_html=response.content)
                    article.parse()
                    text = article.text

            except Exception as e :
                text = descriptions[i]
            if text == '' :
                text = descriptions[i]
            data['text'] = text
            papers.append(data)
        return papers

    def news_collection(self):
        """
        Collects news articles, processes them, and optionally saves them.

        This method fetches articles, extracts relevant information, and uses the parent class's
        `news_collection` method to save the articles if a save path is provided.
        """
        self.fetch_articles()
        news = self.scrapping(self.links, self.dates, self.times, self.descriptions,  self.titles)
        super(NewsApiScraper, self).news_collection(news)
        