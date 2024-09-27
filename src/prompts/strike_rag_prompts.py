from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import  JsonOutputParser
from output_parsers import AutomotiveSector, BusinessSectors, Company, Temporality, LaborStrike

auto_parser = JsonOutputParser(pydantic_object = AutomotiveSector)
parser_business_sectors = JsonOutputParser(pydantic_object = BusinessSectors)
parser_companies_names = JsonOutputParser(pydantic_object = Company)
tmp_parser = JsonOutputParser(pydantic_object = Temporality)
labor_strike_parser = JsonOutputParser(pydantic_object = LaborStrike)

prompt1 = PromptTemplate(
    template="""Your task is to identify the officially named companies that are experiencing strikes instigated by their own workforce based on given context. Answer this query : "{query}" base on the following context : "{context}".
    Make sure to avoid using variations of names mentioned in the context.Use the exact name of the company as it appears in official documents or reputable sources. 
    For instance, if you know that a particular company goes by its full legal name, use that instead of abbreviations or nicknames. If there isn't a specific company mentioned in the context that is undergoing a strike, your response should be 'None'. 
    Additionally, please provide the city and country where the strike is occurring, taking place, or expected to happen. Present your answer in JSON format as the following instructions format following instructions format : {format_instructions}.""",
    input_variables=["query", "context"],
    partial_variables={"format_instructions": parser_companies_names.get_format_instructions()},
    )

prompt2  = PromptTemplate(
        template="""You are an expert in finding the main sectors of a given company. Answer the following query : {query2}
        base on the following context :  {context2}. The output must be at all cost in json format as the following instructions format : {format_instructions}.""",
        input_variables=["query2", "context4"],
        partial_variables={"format_instructions": parser_business_sectors.get_format_instructions()},
    )

prompt3 = PromptTemplate(
        template="""You are an expert in analyzing if any sectors related to car making industry will be affected by a strike. Answer the following query : {query} base on the following context :  {context} . 
        Your role is to analyse and then answer if a given strike will affected any car making industry. The output must be at all cost in json format as the following instructions format : {format_instructions}.""",
        input_variables=["query", "context"],
        partial_variables={"format_instructions": auto_parser.get_format_instructions()},
    )

prompt4 = PromptTemplate(
        template=""" You are an expert in analyzing dates related to a given strike. Answer the following query : {query4} base on the following context :  {context4} . 
             Your role is to analyse and then say if a strike is ended, ongoing, upcoming. The output must be at all cost in json format as the following instructions format : {format_instructions}. 
             answer 'unknow' if the analysis does not allows you to give an response among 'end', 'ongoing', 'upcoming', 'avoided' or 'unknown'.""",
        input_variables=["query4", "context4"],
        partial_variables={"format_instructions": tmp_parser.get_format_instructions()},
    )
    
prompt5 = PromptTemplate(
    template="""You are an expert in analyzing strike concerning a given company. Your role is to answer yes or no if a given strike concerning a company is a labor strike or not. Answer this query : {query5} base on the following context :  {context5} . 
    The output must be at all cost in json format as the following instructions format following instructions format : {format_instructions}.""",
    input_variables=["query5", "context5"],
    partial_variables={"format_instructions": labor_strike_parser.get_format_instructions()},
    )
    