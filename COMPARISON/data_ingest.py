#!/usr/bin/env python3
"""
A simple script for reading the CSV file exports from Medidata rave for the COMPARISON data
and mapping key fields to the CanDIGv1 clinical/phenotypic data model
"""
import argparse
import os
import os.path
import sys
import csv
import json
from datetime import datetime
from collections import defaultdict
from dateutil import relativedelta

def date_from_datetime(datetime_str):
    """
    Give an string YY/MM/DD HH:MM:SS, return just the date string.
    """
    # doing this in the simplest possible way now - just returning
    # the first part of the string split at whitespace.  No validation
    # done.
    words = datetime_str.split()
    if not words:
        return ""
    return words[0]

def province_from_site(site_str):
    """
    Infers the province from the site string
    """
    site_mapping = {"BCCA Vancouver Cancer Centre": "British Columbia",
                    "Princess Margaret Cancer Centre": "Ontario"}

    result = "Unknown"
    site = site_str.strip()
    if site in site_mapping:
        result = site_mapping[site]

    return result

def outcome_label(patient_id, increment=False):
    """
    Generates current outcome label, using the global
    table_to_counts
    """
    global table_to_counts

    # inside the reading loop, incrementing is handled
    # automatically; but to add final vital status, we
    # need to explicilty increment
    if increment:
        table_to_counts["Outcome"][patient_id] += 1

    count = table_to_counts["Outcome"][patient_id]
    return f"{patient_id}_outcome_{count}"

# Below are the mappings from the CSV files to the elements of the CanDIGv1 data model
# The dictionary has keys for each of the relevant csv files (the DataPageName from
# medidata rave).  Then item is a list of tuples of CanDIGv1 table name, and then mapping
# fields.  E.g.:
#
#    "demographics": [
#        ("Patient", {
#            "patientId": "Subject"
#            "gender": "GENDER_CODE"
#         })]
#
# means that in the medidata rave files, demographics.GENDER_CODE -> Patient.gender
#
# Also, rather than a field name like "Subject", the item to map can be a tuple,
# consisting of a function and a number of fields it takes as parameters:  e.g.
#
#        ("Diagnosis", {
#           "patientId": "Subject",
#           "cancerType": (lambda s: s.lower(), "MALIGNANCY"),
#        })
#
# means that the results in the field MALIGNINANCY are lowercased and then placed into
# Diagnosis.cancerType.  Functions with zero arguments can be useful for setting constants:
#
#             "vitalStatus": (lambda : "Dead",),
#
# will always set the vitalStatus field to "Dead" for patients in that table


section_to_mapping_types = {
    "demographics": [
        ("Patient", {
            "patientId": "Subject",
            "gender": "GENDER_CODE",
            "dateOfBirth": (date_from_datetime, "BIRTH_DATE_YM_INT"),
            "ethnicity": "ETHNICITY_CODE",
            "provinceOfResidence": (province_from_site, "Site")
        }),
        ("Enrollment", {
            "patientId": "Subject",
            "ageAtEnrollment": "WEC_AGE"
        })],

    "diagnosis": [
        ("Diagnosis", {
            "patientId": "Subject",
            "diagnosisDate": (date_from_datetime, "DIAG_PA"),
            "cancerType": (lambda s: s.lower(), "MALIGNANCY"),
            "histology": (lambda s: s.lower(), "HISTO_CYTO_DIAG"),
            "tumorGrade": "GRADE_DIAG",
            "specificStage": "STAGE_DIAG"
        })
    ],

    "systemic therapy log": [
        ("Treatment", {
            "patientId": "Subject",
            "therapeuticModality": (lambda s: s.lower(), "THER_TX_NAME"),
            "startDate": (date_from_datetime, "STRT_DT"),
            "stopDate": (date_from_datetime, "LAST_DATE"),
            "responseToTreatment": "THER_BR"
        })
    ],

    "follow-up patient status": [
        ("Outcome", {
            "dateOfAssessment": (date_from_datetime, "FU_STATUS_DT"),
            "diseaeResponseOrStatus": (lambda s: s.strip('"'), "DISEASE_STATUS"),
            "localId": (outcome_label, "Subject")
        })
    ],

    "tissue collection": [
        ("Sample", {
            "patientId": "Subject",
            "sampleId": "SAMPLE_ID",
            "collectionDate": (date_from_datetime, "SURG_DT"),
            "sampleType": "ARCH_TMR_SITE",
            "cancerType": (lambda s: s.lower(), "CANCER_TYPE_LONG")
        })
    ],

    "death": [
        ("Patient", {
            "patientId": "Subject",
            "dateOfDeath": (date_from_datetime, "DTH_DT")
        }),
        ("Outcome", {
            "patientId": "Subject",
            "vitalStatus": (lambda : "Dead",),
            "dateOfAssessment": (date_from_datetime, "DTH_DT"),
            "localId": (outcome_label, "Subject")
        })
    ]
}

table_to_counts = {"Treatment": defaultdict(int),
                   "Diagnosis": defaultdict(int),
                   "Enrollment": defaultdict(int),
                   "Outcome": defaultdict(int)}
patient_to_data = {}


def update_patient_data(row):
    """
    Updates a patient's data with information provided in <row>.

    :param dict[str, str] row: maps each CSV fieldname to its value in a CSV row
    :return: None
    """
    section = row["DataPageName"].strip().lower()
    if not section in section_to_mapping_types:
        return

    mapping_types = section_to_mapping_types[section]

    patient_id = row["Subject"]
    if patient_id not in patient_to_data:
        patient_to_data[patient_id] = {
            "Patient": {
                "patientId": patient_id
            }
        }
    curr_patient_data = patient_to_data[patient_id]

    for mapping_type in mapping_types:
        mapping_name = mapping_type[0]
        mapping_dict = mapping_type[1]

        counter = None
        if mapping_name in table_to_counts:
            counter = table_to_counts[mapping_name]
            counter[patient_id] += 1

        new_dict = {}
        for key in mapping_dict:
            if isinstance(mapping_dict[key], str):
                new_dict[key] = row[mapping_dict[key]]
            else:  # if the value of the key is of a tuple,
                # function and argument namees
                t = mapping_dict[key]
                function, argitems = t[0], t[1:]
                args = (row[item] for item in argitems if item in row)
                new_dict[key] = function(*args)

        if counter:
            new_dict["localId"] = f"{patient_id}_{mapping_name.lower()}_{counter[patient_id]}"

        if mapping_name in curr_patient_data:
            if mapping_name == "Patient":
                curr_patient_data[mapping_name] = {**curr_patient_data[mapping_name], **new_dict}
            elif isinstance(curr_patient_data[mapping_name], list):
                curr_patient_data[mapping_name].append(new_dict)
            else:
                curr_patient_data[mapping_name] = [curr_patient_data[mapping_name], new_dict]
        else:
            curr_patient_data[mapping_name] = new_dict


def main():
    """
    Read in a directory of medidata rave CSV files in inputdir, and output
    a JSON file containing the clin/phen data in CanDIGv1 format
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('inputdir', help='path to directory containing input files in CSV format')
    parser.add_argument('output', help='path to output file in JSON format',
                        type=argparse.FileType('w'), default=sys.stdout)
    args = parser.parse_args()

    input_files_dir = args.inputdir
    outfile = args.output

    try:
        input_files = os.listdir(input_files_dir)
    except OSError as e:
        print(f'Error accessing {input_files_dir}: ', e)
        sys.exit(1)

    for input_file in input_files:
        with open(os.path.join(input_files_dir, input_file), 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                update_patient_data(row)

    # update vital status and keys that depend on same
    for patient_id in patient_to_data:
        new_local_id = outcome_label(patient_id, increment=True)
        if not "dateOfDeath" in patient_to_data[patient_id]["Patient"]:
            if not "Outcome" in patient_to_data[patient_id]:
                patient_to_data[patient_id]["Outcome"] = {"localId": new_local_id}

            outcomes = patient_to_data[patient_id]["Outcome"]
            if isinstance(outcomes, dict):
                patient_to_data[patient_id]["Outcome"]["vitalStatus"] = "Alive"
            elif isinstance(outcomes, list):
                patient_to_data[patient_id]["Outcome"][-1]["vitalStatus"] = "Alive"
        else:
            new_dict = {"vitalStatus": "Dead", "localId": new_local_id}
            if "Diagnosis" in patient_to_data[patient_id] and\
                    len(patient_to_data[patient_id]["Diagnosis"]["diagnosisDate"]) > 0:
                diagnosis_date = datetime.strptime(patient_to_data[patient_id]["Diagnosis"]["diagnosisDate"], "%m/%d/%Y")
                death_date = datetime.strptime(patient_to_data[patient_id]["Patient"]["dateOfDeath"], "%m/%d/%Y")
                new_dict["dateOfAssessment"] = date_from_datetime(str(death_date))
                dates_diff = relativedelta.relativedelta(death_date, diagnosis_date)
                survival_in_months = (dates_diff.years * 12) + dates_diff.months + (dates_diff.days / 30)
                new_dict["overallSurvivalInMonths"] = str(survival_in_months)

            if not "Outcome" in patient_to_data[patient_id]:
                patient_to_data[patient_id]["Outcome"] = new_dict
            elif isinstance(patient_to_data[patient_id]["Outcome"], dict):
                patient_to_data[patient_id]["Outcome"]["overallSurvivalInMonths"] = new_dict["overallSurvivalInMonths"]
            elif isinstance(patient_to_data[patient_id]["Outcome"], list):
                patient_to_data[patient_id]["Outcome"][-1]["overallSurvivalInMonths"] = new_dict["overallSurvivalInMonths"]

    output_dict = {"metadata": list(patient_to_data.values())}
    json.dump(output_dict, outfile)


if __name__ == '__main__':
    main()
