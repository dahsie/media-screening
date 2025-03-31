# Install

We have to branch :
* Master : This branch work on **GCP**
* Dataiku : This branch is a dataiku version. Threre are some differences between the two branch. For exemple, requests are made to get access to **Gemini**, which is not the case when we are already on **GCP**

## Install all branches
git clone --branch test --single-branch https://github.com/dahsie/media-screening.git

## Install only Dataiku branch :
git clone --branch dataiku --single-branch https://github.com/dahsie/media-screening.git

## Install only Master branch :
git clone --branch master --single-branch https://github.com/dahsie/media-screening.git


## Creating configuration file.
In this part, we translate each keywords to some languages, depending on the list of language code we have in our disponsible.
dict_config = {}
dict_config['keywords'] = ['strike', 'picket line', 'employee protest']
dict_config['country_lang'] = [
    {'country': 'BE','lang': ['fr']}, # Belgium
    {'country': 'CH','lang': ['fr', 'de', 'it']}, # Searching news with differentes languge in the same country where threre are several official language
    {'country': 'BG','lang': ['bg']},  # Bulgaria
    {'country': 'BR','lang': ['pt']},