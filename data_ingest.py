import argparse
import sys
import csv
import json


patient_mapping = {
    "patientId": "Patient ID",
    "gender": "SEX",
    "otherIds": "PATIENT DISPLAY NAME"
}

enrollment_mapping = {
    "patientId": "Patient ID",
    "ageAtEnrollment": "AGE",
    "localId": lambda _, dictionary: dictionary["patientId"] + "_enrollment_0"
}

sample_mapping = {
    "patientId": "Patient ID",
    "sampleId": "Sample ID",
    "cancerType": "CANCER TYPE",
    "cancerSubtype": "CANCER TYPE DETAILED",
    "sampleType": lambda row, *_: row['SAMPLE TYPE'] + " " + row['SAMPLE CLASS'],
    "otherBiobank": "STORAGE"
}

treatment_mapping = {
    "patientId": "Patient ID",
    "unexpectedOrUnusualToxicityDuringTreatment": "IRAE EVENT STATUS",
    "reasonForEndingTheTreatment": "REASON OFF TRIAL",
    "localId": lambda _, dictionary: dictionary["patientId"] + "_treatment_0"
}

outcome_types = [
    "Disease Free Status",
    "RECIST1.1 BEST OVERALL RESPONSE"
]

outcome_nums = [0, 1, 2]

outcome_mapping = {
    "patientId": "Patient ID",
    "overallSurvivalInMonths": "Overall Survival",
    "vitalStatus": "Overall Survival Status",
    "diseaseFreeSurvivalInMonths": "Disease Free Survival",
    "responseCriteriaUsed": lambda *_: outcome_types.pop(0),
    "diseaseResponseOrStatus": lambda row, dictionary: row[dictionary["responseCriteriaUsed"]],
    "localId": lambda _, dictionary: dictionary["patientId"] + "_outcome_" + str(outcome_nums.pop(0))
}

labtest_event_types = [
    "BASELINE_TUMOR_CD4 (% of CD3)",
    "BASELINE_TUMOR_CD8 (% of CD3)",
    "BASELINE_TUMOR_PD1 (% CD8)"
]

labtest_nums = [0, 1, 2]

labtest_mapping = {
    "patientId": "Patient ID",
    "eventType": lambda *_: labtest_event_types.pop(0),
    "timePoint": lambda *_: "Baseline",
    "testResults": lambda row, dictionary: row[dictionary["eventType"]],
    "localId": lambda _, dictionary: dictionary["patientId"] + "_labtest_" + str(labtest_nums.pop(0))
}


def get_dict(mapping, row):
    """
    Returns a dictionary with values in <row> mapped to their corresponding keys in <mapping> (if there is one).

    :param dict[str, str | (dict[str, str], dict[str, str]) -> str] mapping: maps JSON key names to CSV fieldnames
    :param dict[str, str] row: maps each CSV fieldname to its value in a CSV row
    :return: values in a CSV row mapped to their corresponding JSON keys (if there is one)
    :rtype: dict[str, str]
    """
    return_dict = {}
    for key in mapping:
        if type(mapping[key]) == str:
            return_dict[key] = row[mapping[key]]
        else:  # if the value of the key is of a function type
            return_dict[key] = mapping[key](row, return_dict)

    return return_dict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input-file', help='path to input file in CSV format')
    parser.add_argument('output-file', help='path to output file in JSON format')
    args = parser.parse_args()

    input_file = getattr(args, 'input-file')
    output_file = getattr(args, 'output-file')

    csv_file = None
    try:
        csv_file = open(input_file)
        reader = csv.DictReader(csv_file)
        output_dict = {
            "metadata": []
        }
        for row in reader:
            row = dict(row)
            output_dict['metadata'].append(
                {
                    "Patient": get_dict(patient_mapping, row),
                    "Enrollment": get_dict(enrollment_mapping, row),
                    "Sample": get_dict(sample_mapping, row),
                    "Treatment": get_dict(treatment_mapping, row),
                    "Outcome": [
                        get_dict(outcome_mapping, row),
                        get_dict(outcome_mapping, row)
                    ],
                    "Labtest": [
                        get_dict(labtest_mapping, row),
                        get_dict(labtest_mapping, row),
                        get_dict(labtest_mapping, row)
                    ]
                }
            )

            # reset outcomes and labtests to their original state for the next iteration
            global outcome_types, labtest_event_types, outcome_nums, labtest_nums
            outcome_types = [
                "Disease Free Status",
                "RECIST1.1 BEST OVERALL RESPONSE"
            ]
            labtest_event_types = [
                "BASELINE_TUMOR_CD4 (% of CD3)",
                "BASELINE_TUMOR_CD8 (% of CD3)",
                "BASELINE_TUMOR_PD1 (% CD8)"
            ]

            outcome_nums = [0, 1, 2]
            labtest_nums = [0, 1, 2]

        json_file = None
        try:
            json_file = open(output_file, 'w')
            json.dump(output_dict, json_file)
        except OSError as e:
            print(f'Error opening {output_file}: ', e)
            sys.exit(1)
        finally:
            if json_file:
                json_file.close()

    except OSError as e:
        print(f'Error opening {input_file}: ', e)
        sys.exit(1)
    finally:
        if csv_file:
            csv_file.close()


if __name__ == '__main__':
    main()
