import requests 
from bs4 import BeautifulSoup

url = "https://ans-elblag.pl/"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
print(soup.title.text)