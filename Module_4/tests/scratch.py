from src.website.app import app
from bs4 import BeautifulSoup
import re

with app.test_client() as client:
  response = client.get('/')
  soup = BeautifulSoup(response.data, "html.parser")
  query_divs = soup.find_all("div", class_="query")
  for query_div in query_divs:
    question = query_div.find("h3")
    if "percent" in question.text:
      print(question.text)
      answer = query_div.find("p")
      print(answer)
      re.search(r"Answer:\s*(-?\d+\.\d{2})$", answer.strip())

  