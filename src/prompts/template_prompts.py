"""
For news event, you must provide some prompts to indicate how the model should deal with each question. A specifque prompt is provid for each question.
So if we have 5 five question, it means we must also have 5 prompts, a prompt for each question. 
The prompt also provide a schema that indicate how each question must be parsed. This schema is the objet of 'output_parsers' those objects are instance 
of those class which can be find here 'media/src/ouput_parsers/output_parsers.py'. 

"""

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import  JsonOutputParser
from media.src.output_parsers.output_parsers import Company




#A tampleate exmple of output_parser

new_parser = JsonOutputParser(pydantic_object = "Add pydantique object, which can be find here 'media/src/ouput_parsers/output_parsers.py' ")

new_prompt = PromptTemplate(
    template="""Explain how the model should act for given context and query. ... "{query}" .... "{context}".

   explain the format of the  output ... in JSON format ...: {format_instructions}.""",
    input_variables=["query", "context"], # You can change those variabels names 'query' and 'context' but make sure thay there are the same as 'input_variables'. Also you can have 
    ## as many as variables you want.
    partial_variables={"format_instructions": new_parser.get_format_instructions()},
    )

# This an real exemple 

parser_companies_names = JsonOutputParser(pydantic_object = Company)

prompt1 = PromptTemplate(
    template="""Your task is to identify the officially named companies that are experiencing strikes instigated by their own workforce based on given context. Answer this query : "{query}" base on the following context : "{context}".
    Make sure to avoid using variations of names mentioned in the context.Use the exact name of the company as it appears in official documents or reputable sources. 
    For instance, if you know that a particular company goes by its full legal name, use that instead of abbreviations or nicknames. If there isn't a specific company mentioned in the context that is undergoing a strike, your response should be 'None'. 
    Additionally, please provide the city and country where the strike is occurring, taking place, or expected to happen. Present your answer in JSON format as the following instructions format following instructions format : {format_instructions}.""",
    input_variables=["query", "context"],
    partial_variables={"format_instructions": parser_companies_names.get_format_instructions()},
    )
