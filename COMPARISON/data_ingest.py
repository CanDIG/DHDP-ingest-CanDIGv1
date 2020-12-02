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
# means that in the medidata rave files, demographics.GENDER_CODE -> Patient.patientId
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
            "cancerType": "MALIGNANCY",
            "histology": "HISTO_CYTO_DIAG",
            "tumorGrade": "GRADE_DIAG",
            "specificStage": "STAGE_DIAG"
        })
    ],

    "systemic therapy log": [
        ("Treatment", {
            "patientId": "Subject",
            "therapeuticModality": "THER_TX_NAME",
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
            "cancerType": "CANCER_TYPE_LONG"
        })
    ],

    "death": [
        ("Patient", {
            "patientId": "Subject",
            "dateOfDeath": "DTH_DT"
        }),
        ("Outcome", {
            "patientId": "Subject",
            "vitalStatus": lambda x: "Dead"
        })
    ]
}

patient_to_id_nums = {}
patient_to_data = {}
dead_patients = set()


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
    if patient_id not in patient_to_id_nums:
        patient_to_id_nums[patient_id] = dict.fromkeys(section_to_mapping_types.keys(), 0)

    if patient_id not in patient_to_data:
        patient_to_data[patient_id] = {
            "Patient": {
                "patientId": patient_id
            }
        }
    curr_patient_data = patient_to_data[patient_id]

    increment_id_num = False
    for mapping_type in mapping_types:
        mapping_name = mapping_type[0]
        mapping_dict = mapping_type[1]

        new_dict = {}
        for key in mapping_dict:
            if isinstance(mapping_dict[key], str):
                new_dict[key] = row[mapping_dict[key]]
            else:  # if the value of the key is of a function type
                args = []
                new_id = section.replace(" ", "_") + "_"
                new_id += str(patient_to_id_nums[patient_id][section])
                args.insert(0, new_id)
                new_dict[key] = mapping_dict[key](*args)
                increment_id_num = True

        if mapping_name in curr_patient_data:
            if mapping_name == "Patient":
                curr_patient_data[mapping_name] = {**curr_patient_data[mapping_name], **new_dict}
            elif isinstance(curr_patient_data[mapping_name], list):
                curr_patient_data[mapping_name].append(new_dict)
            else:
                curr_patient_data[mapping_name] = [curr_patient_data[mapping_name], new_dict]
        else:
            curr_patient_data[mapping_name] = new_dict

        if mapping_name == "Outcome" and patient_to_data[patient_id]["Outcome"]["vitalStatus"].strip().lower() == "dead":
            dead_patients.add(patient_id)

    if increment_id_num:
        patient_to_id_nums[patient_id][section] += 1


def main():
    """
    Read in a directory of medidata rave CSV files in inputdir, and output
    a JSON file containing the clin/phen data in CanDIGv1 format
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('inputdir', help='path to directory containing input files in CSV format')
    parser.add_argument('output', help='path to output file in JSON format', type=argparse.FileType('w'), default=sys.stdout)
    args = parser.parse_args()

    input_files_dir = getattr(args, 'inputdir')
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
        if patient not in dead_patients:
            patient_to_data[patient]["Outcome"] = {
                "patientId": patient,
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
