"""
Scrape data from TheGradCafe using Beautiful Soup.
Returns a list of grad school applicant entry data.
"""
import json
from bs4 import BeautifulSoup
import urllib3

def scrape_data(num_data_points: int):
    """ Scrape a user-selected number of datapoints from TheGradCafe"""

    iter_var = 1
    data_points = 0
    BASE_URL = "https://www.thegradcafe.com/survey/?page="
    entries = []
    http = urllib3.PoolManager()

    while data_points < num_data_points:

        # Open GradCafe webpage using try/except
        url = f"{BASE_URL}{str(iter_var)}"
        try:
            page = http.request("GET", url)

            # Generate BeautifulSoup object for webpage
            soup = BeautifulSoup(page.data.decode("utf-8"), features="lxml")

            # Grad data in "tbody" section, each entry comprised of one or more "tr"
            tbodies = soup.find("tbody")
            rows = tbodies.find_all("tr")
            i = 0

            while i < len(rows):
                row = rows[i]

                # Check if row is a main data row (has 5 tds) and extract data
                tds = row.find_all('td')
                if len(tds) == 5:
                    entry = {} # individual applicant entry data


                    entry["school"] = tds[0].get_text(strip=True)
                    program_div = tds[1].find("div")
                    spans = program_div.find_all('span')
                    entry["program"] = spans[0].get_text(strip=True)
                    entry["degree"] = spans[1].get_text(strip=True) if len(spans) > 1 else None
                    entry["date_added"] = tds[2].get_text(strip=True)
                    entry["status"] = tds[3].get_text(strip=True)
                    link_tag = tds[4].find('a', href=True)
                    entry["link"] = "https://www.thegradcafe.com" + link_tag["href"] if link_tag else None

                    # Check for next row (contains additional data if it exists)
                    metadata_row = rows[i + 1] if (i + 1 < len(rows)) else None
                    if metadata_row and "colspan" in metadata_row.get("class", []) or metadata_row.find("td", colspan=True):
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
                    i += 3  # iterate past metadata and comment rows

                else:
                    i += 1  # skip non-data rows

            iter_var += 1
            data_points = len(entries)

        except urllib3.exceptions.HTTPError as e:
            print("HTTP error occurred:", e)

    return entries

def save_data(input_data: list, output_file: str):
    """ Save scraped data into json file"""
    data_json = json.dumps(input_data, indent=4) # convert list data to json
    with open(output_file, "w") as writer:
        writer.write(data_json)

if __name__ == "__main__":
    grad_data = scrape_data(10000) # enter desired number of datapoints
    FILE_NAME = "applicant_data_messy.json"
    save_data(grad_data, FILE_NAME)
