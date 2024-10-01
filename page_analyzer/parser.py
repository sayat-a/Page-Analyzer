import requests
from bs4 import BeautifulSoup


def parse_url(url):
    response = requests.get(url)
    response.raise_for_status()
    status_code = response.status_code
    soup = BeautifulSoup(response.text, 'html.parser')
    h1 = soup.h1.string if soup.h1 else ''
    title = soup.title.string if soup.title else ''
    description = soup.find('meta', attrs={'name': 'description'})
    description = description['content'] if description else ''
    result = {
        'status_code': status_code,
        'h1': h1,
        'title': title,
        'description': description
              }
    return result
