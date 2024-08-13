
import sys
sys.path.append("/home/jupyter/news/src")

from utils import create_logger

logger = create_logger(__name__, 'matching.log')


import pandas as pd
from tqdm import tqdm

class Matching :
    """
    A class to match news articles with supplier information based on company names, cities, and countries.

    Attributes:
    -----------
        index (list[int]): A list of indices corresponding to matched companies in the news dataset.
        matched_companies (list[str]): A list of company names that have been matched with the news dataset.
        matched_companies_index (list[int]): A list of indices in the news dataset where companies have been matched.
        matched_companies_cites (list[list[str]]): A list of lists containing city names associated with matched companies.
        matched_companies_countries (list[list[str]]): A list of lists containing country names associated with matched companies.

    Methods:
    --------
        __init__():
            Initializes the Matching class with empty attributes for tracking matched companies and their details.
        
        __preprocess(liste: list) -> list:
            Preprocesses a list of strings by converting them to lowercase and removing extra whitespace.

        __add_matched_company(company: str, index1: int, article_countries: list[str], article_cities: list[str], set_news: list[dict]):
            Adds a matched company to the internal lists and updates the news dataset.
        
        __match(set_news: list[dict], suppliers: dict) -> tuple[dict, list[dict]]:
            Matches companies mentioned in the news dataset with the list of suppliers and updates the news dataset with matching information.
        
        match(set_news: list[dict], dataframe: pd.DataFrame):
            Matches companies in the news dataset with supplier information from a DataFrame and updates the internal intersect and results attributes.
    """
    
    def __init__(self) :
        """
        """
        self.index : list[int] = []
        self.matched_companies : list[str] = []
        self.matched_companies_index : list[str] = []
        self.matched_companies_cites : list[list[str]] = []
        self.matched_companies_countries : list[list[str]] = []
        
    def __preprocess(self, liste :list) -> list:
        """
        Preprocesses a list of strings by converting them to lowercase and removing extra whitespace.

        Args:
            liste (list): A list of strings to be processed.
        Returns:
            list: A list of preprocessed strings.
        """
        suppliers = []
        for item in liste:
            string = " ".join(item.split())
            suppliers.append(string.lower().strip())
        return suppliers
  
    
    def __add_matched_company(self, company: str, index1: int, article_countries: list[str], article_cities: list[str], set_news : list[dict]):
        """
        Adds a matched company to the internal lists and updates the news dataset.

        Args:
            company (str): The name of the matched company.
            index1 (int): The index of the news item where the company was matched.
            article_countries (list[str]): A list of countries mentioned in the news article.
            article_cities (list[str]): A list of cities mentioned in the news article.
            set_news (list[dict]): The news dataset being updated with matching information.
        """
        
        self.matched_companies.append(company)
        self.matched_companies_index.append(index1)
        self.matched_companies_countries.append(article_countries)
        self.matched_companies_cites.append(article_cities)
        set_news[index1]['supplier'] = 'yes'
        
    def __match(self,set_news : list[dict], suppliers : dict) -> list[dict] :
        """
        Matches companies mentioned in the news dataset with the list of suppliers.

        Args:
            set_news (list[dict]): A list of news articles, each represented as a dictionary.
            suppliers (dict): A dictionary containing supplier information including names, cities, countries, and tiers.
        Returns:
            tuple: A tuple containing:
                - A dictionary of intersected suppliers.
                - The updated news dataset with matching information.
        """
        suppliers_cities, suppliers_countries, list_of_suppliers , tiers =  suppliers["suppliers_cities"], suppliers["suppliers_countries"], suppliers["suppliers_names"], suppliers["suppiers_tiers"]
        
        intersect =dict()
        for index1, news in tqdm(enumerate(set_news)) :
            
            company = news['impacted_company'].lower().strip() if news['impacted_company'] !='' else '' # a revoir
            core_name = news['core_company'].lower().strip() if news['core_company'] !='' else company # a revoir
            article_cities, article_countries = [],[]
            for location in news['locations'] :
                article_cities.append(location['city'].lower())
                article_countries.append(location['country'].lower())
            
            set_news[index1]['supplier'] = 'no'
            set_news[index1]['matching_level'] = 'none'

            list_of_companies, ll  = [],[]
            keys = intersect.keys()
            
            if  company in keys : 
                self.__add_matched_company(company, index1, article_countries, article_cities, set_news)

            else:

                for index3, supplier in enumerate(list_of_suppliers):

                    splits_suppliers = supplier.split()
            
                    if company == supplier  or core_name == supplier or company in  splits_suppliers or core_name in  splits_suppliers :

                        if supplier not in ll:
                            ll.append(supplier)
                            list_of_companies.append({'company' : supplier, 'city' :suppliers_cities[index3], 'country' : suppliers_countries[index3], 'tier' :tiers[index3]})
                            
                        self.__add_matched_company(company, index1, article_countries, article_cities, set_news)
                        set_news[index1]['supplier']= 'yes'
                        set_news[index1]['tier']= tiers[index3]

                if len(ll) !=0:
                    intersect[company] = list_of_companies
       
        for index, item in enumerate(self.matched_companies):
        
            index1 = self.matched_companies_index[index]
            set_news[index1][f'matching_level'] = 'company'
            suppliers = intersect[item]
            
            for sub_company in suppliers :
                if sub_company['country'] != '' and  sub_company['country'] in self.matched_companies_countries[index]:
                    set_news[index1][f'matching_level'] = 'company-country'
                elif sub_company['city'] != '' and sub_company['city'] in self.matched_companies_cites[index] and sub_company['country'] != '' and  sub_company['country'] in self.matched_companies_countries[index] :
                    set_news[index1][f'matching_level'] = 'company-city-country'
                    break
    
        return intersect, set_news
        
        
        self.intersect = intersect
        self.results = set_news
        
    def match(self, set_news : list[dict], dataframe: pd.DataFrame):
        """
        Matches companies in the news dataset with supplier information from a DataFrame.

        Args:
            set_news (list[dict]): A list of news articles, each represented as a dictionary.
            dataframe (pd.DataFrame): A DataFrame containing supplier information with columns for country, city, suggested name, and tier.

        Updates:
            self.intersect: A dictionary of intersected suppliers.
            self.results: The updated news dataset with matching information.
        """
        suppliers = {
            "suppliers_countries" : self.__preprocess(list(dataframe['country'])),
            "suppliers_cities" : self.__preprocess(list(dataframe['city'])),
            "suppliers_names" : self.__preprocess(list(dataframe['suggested_name'])),
            "suppiers_tiers" : self.__preprocess(list(dataframe['tier']))
        }
        
        self.intersect, self.results = self.__match(set_news = set_news, suppliers=suppliers)