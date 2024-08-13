

import sys
sys.path.append("/home/jupyter/news/src")

from utils import create_logger

logger = create_logger(__name__, 'filtering.log')

from datetime import datetime
import json

class Filter :
    
    """
    A class to filter a list of dictionaries based on a decision function and save the results to a JSON file.

    Attributes:
    -----------
        __desirable (list[str]): A list of dictionaries that meet the criteria defined by the decision function.
        __non_desirable (list[str]): A list of dictionaries that do not meet the criteria defined by the decision function.
        __decision_function (callable): A function used to determine if a dictionary meets the criteria.
        __decision_function_args (dict): Arguments to be passed to the decision function.
        empty_companie_name_index (list[int]): Indices of dictionaries in the input list that should be marked as non-desirable.
        filename (str, optional): The base filename to use when saving the results to a JSON file.
        __results (list[str], optional): The combined list of desirable and non-desirable dictionaries after filtering.

    Methods:
    --------
        __init__(empty_companie_name_index: list[int], decision_function_args: dict, decision_function: callable, filename: str = None):
            Initializes the Filter class with the specified decision function and its arguments, empty company name indices, and optional filename.

        filtering(liste_dict: list[dict], key: str = 'impacted_business_sectors') -> None:
            Filters the input list of dictionaries based on whether any words in the specified key are present in a predefined discard list.
            Updates the internal lists of desirable and non-desirable dictionaries, and saves the results to a JSON file if a filename is provided.

        save_to_json(data_to_save: list[dict], filename: str) -> None:
            Saves the input list of dictionaries to a JSON file with the specified filename.
            
    Properties:
    -----------
        desirable:
            Returns the list of dictionaries that meet the criteria defined by the decision function.

        non_desirable:
            Returns the list of dictionaries that do not meet the criteria defined by the decision function.

        results:
            Returns the combined list of desirable and non-desirable dictionaries after filtering.
    """
    def __init__(self, empty_companie_name_index : list[int], decision_function_args : dict, decision_function: callable , filename :str = None) :
        """
        Initializes the Filter class with the specified decision function and its arguments, empty company name indices, and optional filename.

        Args:
            empty_companie_name_index (list[int]): Indices of dictionaries in the input list that should be marked as non-desirable.
            decision_function_args (dict): Arguments to be passed to the decision function.
            decision_function (callable): A function used to determine if a dictionary meets the criteria.
            filename (str, optional): The base filename to use when saving the results to a JSON file.
        """
        self.__desirable: list[str] =[]
        self.__non_desirable: list[str] = []
        self.__decision_function = decision_function
        self.__decision_function_args: dict = decision_function_args
        self.empty_companie_name_index = empty_companie_name_index
        self.filename = filename
        self.__results: list[str] = None
    
    def filtering(self, liste_dict : list[dict]) -> None :
        """
        Filters the input list of dictionaries based on whether any words in the specified key are present in a predefined discard list.

        For each dictionary in the input list, this method splits the value associated with the specified key into words.
        If none of these words are present in SECTORS_TO_DISCARD, the dictionary is added to the desirable list.
        Otherwise, it is added to the non_desirable list.

        Args:
            liste_dict (list[dict]): The list of dictionaries to be filtered.

        Returns:
            list[dict]: The combined list of desirable and non-desirable dictionaries after filtering.
        """
        # print(liste_dict[0].keys())
        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        base_id = current_datetime.replace('-', '').replace('_', '')
        for index, item in enumerate(liste_dict):
            
            item['id'] = f"{index}-{base_id}"

            if self.__decision_function(item, self.__decision_function_args):
                item['relevant'] = 'yes'
                self.__desirable.append(item)
            else :
                item['relevant'] = 'no'
                self.__non_desirable.append(item)
    
        for index in self.empty_companie_name_index :
            item = liste_dict[index]
            item['relevant'] = 'no'

        results = self.__desirable + self.__non_desirable
        
        if self.filename is not None:
            fname = f"{self.filename+ current_datetime}.json"
            self.save_to_json(data_to_save= results, filename = fname)
        
        self.__results = results
        return results
        
    def save_to_json(self,data_to_save: list[dict], filename : str) -> None :
        """Saves the input list of dictionaries to a JSON file with the specified filename.
         Args:
            dat_to_save (list[dict]): The list of dictionaries to be saved.
            filename (str): The name of the file to save the data to.
        """
        with open(filename, "w") as final:
            json.dump(data_to_save, final, indent=4)
            print("saved !")
            
    #--------------------------------------- PROPERTIES --------------------------------------------------------------------
    
    @property
    def desirable(self) -> list[dict]:
        return self.__desirable
    
    @property
    def non_desirable(self) -> list[dict] :
        return self.__non_desirable
        
    @property
    def results(self) -> list[dict]:
        return self.__results