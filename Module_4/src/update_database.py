"""
Update the database with new data scraped from GradCafe.
Comprises determining most recent entry in database, scraping new data from GradCafe, performing initial clean on data, and applying LLM to data.
"""
import os
import re
from sre_constants import NOT_LITERAL
import psycopg
import json
from bs4 import BeautifulSoup
import urllib3

# Part 1: Determine most recent entry in database currently (based on url entry id).

# Connect to the database.
conn = psycopg.connect(os.environ["DATABASE_URL"])


def find_recent():
  """Function to find most recent entry in database."""

  # Create a cursor object.
  with conn.cursor() as cur:
    # Query to get all URLs from the database.
    cur.execute("SELECT url FROM applicants WHERE url IS NOT NULL;")
    urls = cur.fetchall()

    if not urls:
      return None

    max_number = 0
    recent_url = None

    # Extract number from each URL and find the maximum.
    for (url, ) in urls:
      try:
        url_parts = url.split('/')
        if url_parts:
          number = int(url_parts[-1])
          if number > max_number:
            max_number = number
            recent_url = url
      except (ValueError, IndexError):
        # Skip URLs that don't have a valid number at the end.
        continue

  return int(max_number)


# Part 2: Scrape new data from TheGradCafe. "New" means data that is not already contained in our database, which is determined by entry id (found at end of entry url).


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

    # Open GradCafe webpage using try/except.
    url = f"{BASE_URL}{str(iter_var)}"
    try:
      page = http.request("GET", url)

      # Generate BeautifulSoup object for webpage.
      soup = BeautifulSoup(page.data.decode("utf-8"), features="lxml")

      # Grad data in "tbody" section, each entry comprised of one or more "tr".
      tbodies = soup.find("tbody")
      if not tbodies:
        print(f"No data found on page {iter_var}")
        break

      rows = tbodies.find_all("tr")
      i = 0
      page_entries = 0

      while i < len(rows):
        row = rows[i]

        # Check if row is a main data row (has 5 tds) and extract data.
        tds = row.find_all('td')
        if len(tds) == 5:
          entry = {}

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
          entry["link"] = "https://www.thegradcafe.com" + str(
              link_tag.get("href",
                           "")) if link_tag and link_tag.get("href") else None

          # Extract entry ID from link.
          entry_id = None
          if entry["link"]:
            try:
              entry_id = int(entry["link"].split('/')[-1])
            except (ValueError, IndexError):
              entry_id = None

          # Check if this entry is older than our recent_id.
          if entry_id and entry_id <= recent_id:
            print(
                f"Found entry ID {entry_id} <= recent_id {recent_id}, stopping scrape"
            )
            found_recent_entry = True
            break

          # Check for next row (contains additional data if it exists).
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

          # Check for next (row contains comments if row exists).
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

  return entries


# Part 3: Clean data
def clean_data(raw_data: list):
  """ Convert data to desired format and remove bad data.
  Output data is ready to be procseed by LLM.
  Adapted from Module 2 assignment.
  """

  clean_data_list = []

  for entry in raw_data:
    clean_entry = {}

    # Clean numbers out of school name using Regex.
    RE_NUM_PAT = r"\d"
    if "school" not in entry or re.search(RE_NUM_PAT, entry["school"]) is None:
      pass
    else:
      entry["school"] = re.sub(RE_NUM_PAT, "", entry["school"])

    # Clean HTML tags with Regex.
    RE_TAG_PAT = r"<[^>]+>"
    if entry["comments"] is None:
      pass
    else:
      entry["comments"] = re.sub(RE_TAG_PAT, "", entry["comments"])

    # Old entries use a differemt "term" format
    # (e.g. old:F18, new:Fall 2018), use Regex to standardize.
    RE_TERM_PAT = r"^[A-Za-z]\d{2}$"
    if "semester_year" not in entry or re.search(
        RE_TERM_PAT, entry["semester_year"]) is None:
      pass
    else:
      if entry["semester_year"][0] == "F":
        entry["semester_year"] = f"Fall 20{entry['semester_year'][1:]}"
      elif entry["semester_year"][0] == "S":
        entry["semester_year"] = f"Spring 20{entry['semester_year'][1:]}"

    # Format everything as in assignment brief.
    if "program" in entry and "school" in entry:
      program = entry["program"]
      school = entry["school"]
      clean_entry["program"] = f"{program}, {school}"
    else:
      clean_entry["program"] = None

    clean_entry[
        "comments"] = entry["comments"] if "comments" in entry else None
    clean_entry[
        "date_added"] = entry["date_added"] if "date_added" in entry else None
    clean_entry["url"] = entry["link"] if "link" in entry else None
    clean_entry["status"] = entry["status"] if "status" in entry else None
    clean_entry[
        "term"] = entry["semester_year"] if "semester_year" in entry else None
    clean_entry["US/International"] = entry[
        "citizenship"] if "citizenship" in entry else None
    clean_entry["Degree"] = entry["degree"] if "degree" in entry else None
    clean_entry["GRE"] = entry["GRE"] if "GRE" in entry else None
    clean_entry["GRE_V"] = entry["GRE_V"] if "GRE_V" in entry else None
    clean_entry["GPA"] = entry["GPA"] if "GPA" in entry else None
    clean_entry["GRE_AW"] = entry["GRE_AW"] if "GRE_AW" in entry else None

    clean_data_list.append(clean_entry)

  return clean_data_list


def process_data_with_llm(cleaned_data: list, output_file: str | None = None):
  """
  Process cleaned data through the LLM app.
  """
  import subprocess
  import tempfile
  import os

  # Create temporary files for input and output.
  with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                   delete=False) as temp_input:
    json.dump(cleaned_data, temp_input, indent=2)
    temp_input_path = temp_input.name

  try:
    # Create temporary output file.
    temp_output_path = temp_input_path + '.jsonl'

    # Path to the LLM app
    llm_app_path = os.path.join(os.path.dirname(__file__), 'llm_hosting',
                                'llm_hosting', 'app.py')

    # Run the LLM app to process the data.
    print(
        f"Processing {len(cleaned_data)} entries through LLM for standardization..."
    )
    result = subprocess.run([
        'python', llm_app_path, '--file', temp_input_path, '--out',
        temp_output_path
    ],
                            capture_output=True,
                            text=True,
                            cwd='.')

    if result.returncode != 0:
      print(f"LLM processing failed: {result.stderr}")
      return cleaned_data  # Return original data if processing fails

    # Read the processed JSONL output.
    processed_data = []
    if os.path.exists(temp_output_path):
      with open(temp_output_path, 'r', encoding='utf-8') as f:
        for line in f:
          if line.strip():
            processed_data.append(json.loads(line.strip()))

    # Save to output file if specified
    if output_file:
      with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=4, ensure_ascii=False)
      print(f"LLM-processed data saved to: {output_file}")

    return processed_data

  finally:
    # Clean up temporary files
    for temp_file in [temp_input_path, temp_input_path + '.jsonl']:
      if os.path.exists(temp_file):
        os.unlink(temp_file)


if __name__ == "__main__":
  current_recent = find_recent()

  # Handle the case where there are no URLs in the database
  if current_recent is None:
    # Start from ID 0 if no previous entries exist
    current_recent = 0

  new_results = updated_scrape(current_recent)
  # close connection, proceed with data cleaning
  conn.close()

  # Preliminary clean data
  new_clean_data = clean_data(new_results)

  # Run through LLM
  llm_extend_data = process_data_with_llm(new_clean_data,
                                          "new_llm_extend.json")
