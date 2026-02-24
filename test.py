import requests
from bs4 import BeautifulSoup

response = requests.get('https://api.gold-api.com/price/XAU')