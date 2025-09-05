"""Clean data scraped from GradCafe and return a formatted json object"""

import json
import re

def load_data(input_json:str):
    """Loads data from a json file, returns Python list"""
    with open(input_json, "r") as reader:
        json_data = json.load(reader)
        return json_data


def clean_data(raw_data: list):
    """ Convert data to desired format and remove bad data"""

    clean_data = []

    for entry in raw_data: # each entry one applicant's data
        clean_entry = {} # holds entry after cleaning

        # Clean numbers out of school name using Regex
        RE_NUM_PAT = r"\d"
        if re.search(RE_NUM_PAT, entry["school"]) is None:
            pass
        else:
            entry["school"] = re.sub(RE_NUM_PAT, "", entry["school"])

        # Old entries use a differemt "term" format 
        # (e.g. old:F18, new:Fall 2018), use Regex to standardize
        RE_TERM_PAT = r"^[A-Za-z]\d{2}$"
        if re.search(RE_TERM_PAT, entry["semester_year"]) is None:
            pass
        else:
            if entry["semester_year"][0] == "F":
                entry["semester_year"] = f"Fall 20{entry["semester_year"][1:]}"
            elif entry["semester_year"][0] == "S":
                entry["semester_year"] = f"Spring 20{entry["semester_year"][1:]}"


        # Format everything as in assignment brief
        if "program" in entry and "school" in entry:
            clean_entry["program"] = f"{entry["program"]}, {entry["school"]}"
        else:
            clean_entry["program"] = None

        clean_entry["comments"] = entry["comments"] if "comments" in entry else None
        clean_entry["date_added"] = entry["date_added"] if "date_added" in entry else None
        clean_entry["url"] = entry["link"] if "link" in entry else None
        clean_entry["status"] = entry["status"] if "status" in entry else None
        clean_entry["term"] = entry["semester_year"] if "semester_year" in entry else None
        clean_entry["US/International"] = entry["citizenship"] if "citizenship" in entry else None
        clean_entry["Degree"] = entry["degree"] if "degree" in entry else None
        clean_entry["GRE"] = entry["GRE"] if "GRE" in entry else None
        clean_entry["GRE_V"] = entry["GRE_V"] if "GRE_V" in entry else None
        clean_entry["GPA"] = entry["GPA"] if "GPA" in entry else None
        clean_entry["GRE_AW"] = entry["GRE_AW"] if "GRE_AW" in entry else None

        clean_data.append(clean_entry)

    return clean_data

def save_clean_data(input_data: list, output_file: str):
    data_json = json.dumps(input_data, indent=4) # convert list data to json
    with open(output_file, "w") as writer:
        writer.write(data_json)

if __name__ == "__main__":
    test_data = load_data("applicant_data_messy.json")
    cleaned_data = clean_data(test_data)
    CLEAN_FILE_NAME = "clean_needs_llm.json"
    save_clean_data(cleaned_data, CLEAN_FILE_NAME)
