"""
Update the database with new data scraped from GradCafe.
"""
import os
from sre_constants import NOT_LITERAL
import psycopg2
import json
import json
from bs4 import BeautifulSoup
import urllib3

# Part I: Determine most recent entry in database currently (based on url entry id)

# Connect to the database
conn = psycopg2.connect(os.environ["DATABASE_URL"])


def find_recent():
  """
  Function to find most recent entry in database"""

  # Create a cursor object
  with conn.cursor() as cur:
    # Query to get all URLs from the database
    cur.execute("SELECT url FROM applicants WHERE url IS NOT NULL;")
    urls = cur.fetchall()

    if not urls:
      return None

    max_number = 0
    recent_url = None

    # Extract number from each URL and find the maximum
    for (url, ) in urls:
      try:
        # Extract the number from the end of the URL
        # Split by '/' and get the last part
        url_parts = url.split('/')
        if url_parts:
          # Get the last part and convert to integer
          number = int(url_parts[-1])
          if number > max_number:
            max_number = number
            recent_url = url
      except (ValueError, IndexError):
        # Skip URLs that don't have a valid number at the end
        continue

  return int(max_number)


# Part II: Scrape new data from TheGradCafe. "New" means data that is not already contained in our database, which is determined by entry id (found at end of entry url).


def updated_scrape(recent_id: int):
  """
  Scrape new data from TheGradCafe using Beautiful Soup.
  Function ensures new data by comparing scraped entry id to previous 
  largest entry id (input to the function).
  Returns a list of grad school applicant entry data.
  """
  iter_var = 1
  BASE_URL = "https://www.thegradcafe.com/survey/?page="
  entries = []
  http = urllib3.PoolManager()
  max_pages = 50  # Safety limit to prevent infinite loops
  found_recent_entry = False

  print(
      f"Starting scrape from page 1, looking for entries newer than ID {recent_id}"
  )

  while iter_var <= max_pages and not found_recent_entry:

    # Open GradCafe webpage using try/except
    url = f"{BASE_URL}{str(iter_var)}"
    try:
      page = http.request("GET", url)

      # Generate BeautifulSoup object for webpage
      soup = BeautifulSoup(page.data.decode("utf-8"), features="lxml")

      # Grad data in "tbody" section, each entry comprised of one or more "tr"
      tbodies = soup.find("tbody")
      if not tbodies:
        print(f"No data found on page {iter_var}")
        break

      rows = tbodies.find_all("tr")
      i = 0
      page_entries = 0

      while i < len(rows):
        row = rows[i]

        # Check if row is a main data row (has 5 tds) and extract data
        tds = row.find_all('td')
        if len(tds) == 5:
          entry = {}  # individual applicant entry data

          entry["school"] = tds[0].get_text(strip=True)
          program_div = tds[1].find("div")
          if program_div:
            spans = program_div.find_all('span')
            entry["program"] = spans[0].get_text(strip=True) if spans else ""
            entry["degree"] = spans[1].get_text(
                strip=True) if len(spans) > 1 else None
          else:
            entry["program"] = ""
            entry["degree"] = None

          entry["date_added"] = tds[2].get_text(strip=True)
          entry["status"] = tds[3].get_text(strip=True)
          link_tag = tds[4].find('a', href=True)
          entry["link"] = "https://www.thegradcafe.com" + link_tag[
              "href"] if link_tag else None

          # Extract entry ID from link
          entry_id = None
          if entry["link"]:
            try:
              entry_id = int(entry["link"].split('/')[-1])
            except (ValueError, IndexError):
              entry_id = None

          # Check if this entry is older than our recent_id
          if entry_id and entry_id <= recent_id:
            print(
                f"Found entry ID {entry_id} <= recent_id {recent_id}, stopping scrape"
            )
            found_recent_entry = True
            break

          # Check for next row (contains additional data if it exists)
          metadata_row = rows[i + 1] if (i + 1 < len(rows)) else None
          if metadata_row and ("colspan" in str(metadata_row.get("class", []))
                               or metadata_row.find("td", colspan=True)):
            badges = metadata_row.find_all('div', class_='tw-inline-flex')
            for badge in badges:
              text = badge.get_text(strip=True)
              if "Fall" in text or "Spring" in text:
                entry['semester_year'] = text
              elif "American" in text or "International" in text:
                entry["citizenship"] = text
              elif "GPA" in text:
                entry["GPA"] = text.split()[-1]
              elif "GRE V" in text:
                entry["GRE_V"] = text.split()[-1]
              elif "GRE Q" in text:
                entry["GRE_Q"] = text.split()[-1]
              elif "GRE AW" in text:
                entry["GRE_AW"] = text.split()[-1]
              elif "GRE" in text:
                entry["GRE"] = text.split()[-1]

          # Check for next (row contains comments if row exists)
          comment_row = rows[i + 2] if (i + 2 < len(rows)) else None
          if comment_row and comment_row.find('p'):
            entry["comments"] = comment_row.get_text(strip=True)
          else:
            entry["comments"] = None

          entries.append(entry)
          page_entries += 1
          i += 3  # iterate past metadata and comment rows

        else:
          i += 1  # skip non-data rows

      print(
          f"Page {iter_var}: Found {page_entries} new entries (total: {len(entries)})"
      )
      iter_var += 1

    except urllib3.exceptions.HTTPError as e:
      print(f"HTTP error occurred on page {iter_var}: {e}")
      break
    except Exception as e:
      print(f"Unexpected error on page {iter_var}: {e}")
      break

  # Summary
  if found_recent_entry:
    print(
        f"Scraping completed: Found recent entry, stopped at page {iter_var-1}"
    )
  else:
    print(
        f"Scraping completed: Reached maximum pages ({max_pages}) or no more data"
    )

  print(f"Total new entries found: {len(entries)}")
  return entries


def save_data(input_data: list, output_file: str):
  """ Save scraped data into json file"""
  data_json = json.dumps(input_data, indent=4)  # convert list data to json
  with open(output_file, "w") as writer:
    writer.write(data_json)


# End functions, start processing
current_recent = find_recent()

# Handle the case where there are no URLs in the database
if current_recent is None:
  # Start from ID 0 if no previous entries exist
  current_recent = 0

new_results = updated_scrape(current_recent)
print(new_results)
conn.close()
