
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate(
    template = """You are tasked with creating a very concise summary of an article related to events like 'strike' or 'fire.'
    Since the articles are from the internet, ignore the source, publisher, or any irrelevant details.
    Ensure the summary only includes information directly related to the events (e.g., 'fire' or 'strike') affecting a company.
    Provide an extremely concise summary of no more than {max_tokens} words for the following article: '{text}'.
    Make sure it strictly meets the {max_tokens} words limit.
    """,
    input_variables=["text", "max_tokens"]
)

refine_prompt =  PromptTemplate(template =
    """Your task is to create a concise final summary.
    We have provided an initial summary: {existing_answer}.
    You can refine this summary using the additional context below, if necessary.
    ------------
    {text}
    ------------
    Based on the new context, improve the original summary in English.
    If the context is not helpful, keep the original summary.
    The refined summary must be extremely concise, not exceeding {max_tokens} words. 
    This is a strict requirement.
    """,
    input_variables=["text", "max_tokens"]
)

#prompt_template = """Write a very concise summary of the following text:
#    {text}
#    CONCISE SUMMARY:"""


# refine_template = (
#     "Your job is to produce a final summary of at most 100 words and not beyond.\n"
#     "We have provided an existing summary up to a certain point: {existing_answer}\n"
#     "We have the opportunity to refine the existing summary"
#     "with some more context below.\n"
#     "------------\n"
#     "{text}\n"
#     "------------\n"
#     "Given the new context, refine the original summary in english, the final summary must not exceed 100 words." 
#     "If the context isn't useful, return the original summary." 
# ) 