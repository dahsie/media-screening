from media.src.scraping.newsapiscraper import NewsApiScraper
from media.src.scraping.googlescraper import GoogleScraper
#from googlescraper import *
from typing import Union
import pandas as pd
from tqdm import tqdm
from media.src.utils.utils import copy_log_file
from media.src.utils.utils import create_logger

logger, logfile_path = create_logger(__name__, 'newscollector.log')

class NewsCollector:
    """
    A class to collect news articles using specified scrapers.
    """

    def __init__(self, scraper: Union[GoogleScraper, NewsApiScraper], config :dict, path_to_save = None):
        """Initialises the NewsCollector."""
        self.scraper = scraper
        self.news_config = config
        self.path_to_save = path_to_save
        self.limit : int =30720
        self.logfile_path = logfile_path
        self.scraper_name: str = "googlescraper" if isinstance(self.scraper, GoogleScraper) else "newsAPIscraper"


    def collect_news(self):
        """Collects news articles based on the provided configuration."""
        
        dataframe = None
        logger.info(f'starting news collection with {self.scraper_name}')
        for item in tqdm(self.news_config):
            # print(item)
            self.scraper.country = item['country']
            self.scraper.lang = item['lang']
            logger.info(f"lang = {item['lang']}")
            for query in item['queries']:
                
                self.scraper.query =  query
                self.scraper.news_collection()
                copy_log_file(self.scraper.logfile_path, self.logfile_path)
                print(self.scraper.country, self.scraper.lang, self.scraper.query)
                data_ = self.scraper.articles_dataframe

                data_ = data_.loc[data_['titles'] !='',:] if data_ is not None and len(data_) !=0  else None

                data_ = data_.loc[data_['texts'] !='',:] if data_ is not None and  len(data_) !=0 else None
                data_ = data_.loc[data_['texts'].str.len() < self.limit, :] if data_ is not None and  len(data_) !=0 else None
                if data_ is not None :
                    print(f" data_.shape :{ data_.shape}")
                    logger.info(f" data_.shape :{ data_.shape}")

                if data_ is None or len(data_) == 0:
                    continue
                    
                dataframe = pd.concat([dataframe, data_], axis=0)
          
        if dataframe is not None :
            dataframe.reset_index(inplace=True, drop=True)
            logger.info('data collected successfully!')
            
        self.data = dataframe
       
        if isinstance(self.scraper, GoogleScraper):
            self.scraper.kill_driver()
            logger.info('driver killed successfully')
            
        if self.path_to_save :
            dataframe.to_csv(self.path_to_save, index= False)
            logger.info(f'data saved successfully to :{self.path_to_save}')
        return self.data