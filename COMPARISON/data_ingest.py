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

#
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

section_to_mapping_types = {
    "demographics": [
        ("Patient", {
            "patientId": "Subject",
            "gender": "GENDER_CODE",
            "dateOfBirth": "BIRTH_DATE_YM_INT",
            "ethnicity": "ETHNICITY_CODE_STD"
        }),
        ("Enrollment", {
            "patientId": "Subject",
            "ageAtEnrollment": "WEC_AGE"
        })],

    "diagnosis": [
        ("Diagnosis", {
            "patientId": "Subject",
            "diagnosisDate": "DIAG_PA",
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
            "startDate": "STRT_DT",
            "stopDate": "LAST_DATE",
            "responseToTreatment": "THER_BR"
        })
    ],

    "tissue collection": [
        ("Sample", {
            "patientId": "Subject",
            "sampleId": "SAMPLE_ID",
            "collectionDate": "SURG_DT",
            "sampleType": "ARCH_TMR_SITE",
            "cancerType": (lambda s: s.lower(), "CANCER_TYPE_LONG")
        })
    ],

    "death": [
        ("Patient", {
            "patientId": "Subject",
            "dateOfDeath": "DTH_DT"
        }),
        ("Outcome", {
            "patientId": "Subject",
            "vitalStatus": (lambda : "Dead",),
            "dateOfAssessment": "DTH_DT"
        })
    ]
}

table_to_counts = {"Treatment": defaultdict(int),
                   "Diagnosis": defaultdict(int),
                   "Enrollment": defaultdict(int)}
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
                function = mapping_dict[key][0]
                args = (row[item] for item in t[1:] if item in row)
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
    parser.add_argument('output', help='path to output file in JSON format', type=argparse.FileType('w'), default=sys.stdout)
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

    for patient in patient_to_data:
        if not "Outcome" in patient_to_data[patient]:
            patient_to_data[patient]["Outcome"] = {
                "patientId": patient,
                "localId": f"{patient}_outcome_1",
                "vitalStatus": "Alive"
            }
        else:
            if "Diagnosis" in patient_to_data[patient] and\
                    len(patient_to_data[patient]["Diagnosis"]["diagnosisDate"]) > 0:
                diagnosis_date = datetime.strptime(patient_to_data[patient]["Diagnosis"]["diagnosisDate"].split()[0], "%m/%d/%Y")
                death_date = datetime.strptime(patient_to_data[patient]["Patient"]["dateOfDeath"].split()[0], "%m/%d/%Y")
                dates_diff = relativedelta.relativedelta(death_date, diagnosis_date)
                survival_in_months = (dates_diff.years * 12) + dates_diff.months + (dates_diff.days / 30)
                patient_to_data[patient]["Outcome"]["overallSurvivalInMonths"] = str(survival_in_months)

    output_dict = {"metadata": list(patient_to_data.values())}
    json.dump(output_dict, outfile)

if __name__ == '__main__':
    main()
