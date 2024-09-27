from langchain_core.prompts import PromptTemplate

from langchain_core.output_parsers import  JsonOutputParser
from output_parsers import AutomotiveSector, BusinessSectors, Company, FirePlant

auto_parser = JsonOutputParser(pydantic_object= AutomotiveSector)
parser_business_sectors = JsonOutputParser(pydantic_object=BusinessSectors)
parser_companies_names = JsonOutputParser(pydantic_object=Company)
fire_plant_parser = JsonOutputParser(pydantic_object=FirePlant)

prompt1 = PromptTemplate(
    template="""Your task is to identify the officially named companies that are experiencing fire at factory happened in their factory. Answer this query : "{query}" base on the following context : "{context}".
    Make sure to avoid using variations of names mentioned in the context.Use the exact name of the company as it appears in official documents or reputable sources. 
    For instance, if you know that a particular company goes by its full legal name, use that instead of abbreviations or nicknames. If there isn't a specific company mentioned in the context that is undergoing a fire at it plant, your response should be 'None'. 
    Additionally, please provide the city and country of the compay undergoing the fire. Present your answer in JSON format as the following instructions format following instructions format : {format_instructions}.""",
    input_variables=["query", "context"],
    partial_variables={"format_instructions": parser_companies_names.get_format_instructions()},
    )

prompt2  = PromptTemplate(
        template="""You are an expert in finding the main sectors of the following comapny : "{company2}". Answer the following query : "{query2}".
        base on the following context :  "{context2}". The output must be at all cost in json format as the following instructions format : {format_instructions}.""",
        input_variables=["query2", "company2","context2"],
        partial_variables={"format_instructions": parser_business_sectors.get_format_instructions()},
    )

prompt3 = PromptTemplate(
        template="""You are an expert in analyzing if any sectors related to car making industry will be affected by the fire at "{company}" factory. Answer the following query : "{query}" base on the following context :  "{context}" . 
        The output must be at all cost in json format as the following instructions format : {format_instructions}.""",
        input_variables=["query", "company","context"],
        partial_variables={"format_instructions": auto_parser.get_format_instructions()},
    )

    
prompt5 = PromptTemplate(
    template="""You are an expert in analyzing the fire  at "{company5}". Answer yes or no if this fire concerning a manufacturing company. Answer this query : "{query5}" base on the following context :  "{context5}" . 
    The output must be at all cost in json format as the following instructions format following instructions format : {format_instructions}.""",
    input_variables=["query5", "company5","context5"],
    partial_variables={"format_instructions": fire_plant_parser.get_format_instructions()},
    )