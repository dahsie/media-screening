# Install

## pygooglenews install
git clone https://github.com/kotartemiy/pygooglenews.git

Modify date parser within ./pygooglenews/pygooglenews/__init__.py :
  comment this line : # from dateparser import parse as parse_date
  add a new function within the file : 
    def parse_date(date_string : str):
        return datetime.strptime(date_string, '%Y-%m-%d')

## Install media-screening
git clone --branch test --single-branch https://github.com/dahsie/media-screening.git


