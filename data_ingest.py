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
    "enrollmentApprovalDate": lambda *_: "N/A",
    "ageAtEnrollment": "AGE"
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
    "startDate": lambda *_: "N/A",
    "unexpectedOrUnusualToxicityDuringTreatment": "IRAE EVENT STATUS",
    "reasonForEndingTheTreatment": "REASON OFF TRIAL"
}

outcome_mapping = {
    "patientId": "Patient ID",
    "dateOfAssessment": lambda *_: "N/A",
    "overallSurvivalInMonths": "Overall Survival",
    "vitalStatus": "Overall Survival Status",
    "diseaseFreeSurvivalInMonths": "Disease Free Survival",
    "responseCriteriaUsed": lambda *_: "Disease Free Status",
    "diseaseResponseOrStatus": lambda row, dictionary: row[dictionary["responseCriteriaUsed"]]
}

labtest_mapping = {
    "patientId": "Patient ID",
    "startDate": lambda *_: "N/A",
    "eventType": lambda *_: "BASELINE_TUMOR_CD4 (% of CD3)",
    "timePoint": lambda *_: "Baseline",
    "testResults": lambda row, dictionary: row[dictionary["eventType"]]
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
                    "Outcome": get_dict(outcome_mapping, row),
                    "Labtest": get_dict(labtest_mapping, row)
                }
            )

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
