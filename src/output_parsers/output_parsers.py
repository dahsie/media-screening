
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Literal

class CityCountry(BaseModel):
    """
    Represents a location with a city and a country where an event (strike, fire at factory, etc.) took place

    Attributes:
        city (str): Name of the city.
        country (str): Name of the country.
    """
    city: str
    country: str

class Company(BaseModel):
    """
    Represents a company impacted by an event( strike, fire) with its name and various locations.

    Attributes:
        company (str): Name of the company.
        locations (List[CityCountry]): List of locations (cities and countries) where the company is undergoing an event (strike, fire, etc.).
    """
    company: str
    locations: List[CityCountry]

class BusinessSectors(BaseModel):
    """
    Represents the business sectors that are impacted by an event (strike, fire, flood, etc.).

    Attributes:
        business_sectors (List[str]): List of impacted business sectors.
    """
    business_sectors: List[str]

class AutomotiveSector(BaseModel):
    """
    Represents whether the automotive sector is concerned and the justification.

    Attributes:
        concerned (Literal['yes', 'no']): Indicates if the automotive sector is affected by an event (strike, fire, flood, etc.).
        justification (str): Justification for the answer.
    """
    concerned: Literal['yes', 'no']
    justification: str = Field(description="Justify your answer")

class FirePlant(BaseModel):
    """
    Represents whether the fire at the plant concerns a manufacturing company and the justification.

    Attributes:
        fire_plant (Literal['yes', 'no']): Indicates if the company has really experienced fire on its premises.
        justification (str): Justification for the answer.
    """
    fire_plant: Literal['yes', 'no']
    justification: str = Field(description="Justify your answer")

class Temporality(BaseModel):
    """
    Represents the status of the strike and the justification.

    Attributes:
        strike_status (Literal['ended', 'ongoing', 'upcoming', 'avoided', 'unknown']): Status of the strike.
        justification (str): Justification for the answer.
    """
    strike_status: Literal['ended', 'ongoing', 'upcoming', 'avoided', 'unknown']
    justification: str = Field(description="Justify your answer")

class LaborStrike(BaseModel):
    """
    Represents whether the strike is a labor strike and the justification.

    Attributes:
        labor_strike (Literal['yes', 'no']): Indicates if the strike is a labor strike.
        justification (str): Justification for the answer.
    """
    labor_strike: Literal['yes', 'no']
    justification: str = Field(description="Justify your answer")
        
#TODO : Add another class to indicate any news field
