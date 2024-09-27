"""Provide here all questions you the model to answer in order to make a decision if an event is relevant or not
"""

# TODO

# The questions bellow are an exmple for treating  'strike' event
query1 = "What is the primary company affected by the recent auto industry strike? Please provide at most one company that is directly impacted."

query2 = "In which sectors does '{company}' operate, and how are they impacted by the strike? Please provide the top 2 sectors."


query3 = """Given that the main sectors of '{company}' are :  '{business_sectors}',   is the car makering industry concerned by the strike? (yes/no). Think step by step if the product of {company} can be use in car making before answering."""

query4 = "What is the current status of the strike at '{company}'? Is it 'ended', 'ongoing', 'upcoming', 'avoided' or 'unknown'?"

query5 = "Answer yes or no if the '{company}' strike  is a labor strike. "