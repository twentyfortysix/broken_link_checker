# Broken Links Checker

A Python web crawler using Scrapy to check for broken links on websites.

## Requirements

- Python 3.9+
- Virtual Environment

## Installation

1. Clone the repository
```bash
git clone [repository-url]
cd broken-links-checker

python3 -m venv env
source env/bin/activate

pip install -r requirements.txt

source env/bin/activate

update url in the spider 

scrapy crawl linkchecker

open the output.csv in spreadshet and do the manual job