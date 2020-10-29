import argparse
from datetime import datetime
import os
import sys
import csv
import json

patient_mapping_0 = {
    "gender": "PRSN_GENDER_TXT_TP",
    "dateOfBirth": "PER_BIR_DT",
    "race": "RACE_CAT_TXT_STD",
    "ethnicity": "ETH_GRP_CAT_TXT_STD"
}

patient_mapping_1 = {
    "dateOfDeath": "DEATH_DT"
}

sample_mapping_0 = {
    "patientId": "Subject",
    "sampleId": lambda sample_id: sample_id,
    "collectionDate": "BX_DT",
    "anatomicSiteTheSampleObtainedFrom": "BIOP_ANA_PERF_NAM_STD"
}

sample_mapping_1 = {
    "patientId": "Subject",
    "sampleId": lambda sample_id: sample_id,
    "collectionDate": "BL_SPEC_COLL_DT"
}

treatment_mapping_0 = {
    "patientId": "Subject",
    "stopDate": "OTX_DATE",
    "reasonForEndingTheTreatment": "OFF_TX_RSN_SPEC",
    "localId": lambda local_id: local_id
}

treatment_mapping_1 = {
    "patientId": "Subject",
    "startDate": "INTVN_BEG_DT",
    "localId": lambda local_id: local_id
}

outcome_mapping = {
    "patientId": "Subject",
    "vitalStatus": "PART_VITAL_STAT_TP",
    "localId": lambda local_id: local_id
}

diagnosis_mapping = {
    "patientId": "Subject",
    "diagnosisDate": "CURRENT_DZ_P_DX_DT",
    "cancerSite": "PRIM_DZ_ANAT_SITE_NM_STD",
    "localId": lambda local_id: local_id
}

immunotherapy_mapping_0 = {
    "patientId": "Subject",
    "courseNumber": "CRSE_NUM",
    "startDate": "TX_STT_DT",
    "localId": lambda local_id: local_id
}

immunotherapy_mapping_1 = {
    "patientId": "Subject",
    "immunotherapyType": "AGT_NAME",
    "localId": lambda local_id: local_id
}

labtest_mapping_0 = {
    "patientId": "Subject",
    "recordingDate": "IMG_PROC_DT",
    "localId": lambda local_id, *_: local_id
}

labtest_mapping_1 = {
    "patientId": "Subject",
    "testResults": "MSRBL_IND",
    "localId": lambda local_id, *_: local_id,
    "eventType": lambda _id, method: "RECISTv1.1 " + method + " MSRBL_IND"
}

labtest_mapping_2 = {
    "patientId": "Subject",
    "testResults": "TGT_NONTGT_IDN_TXT",
    "localId": lambda local_id, *_: local_id,
    "eventType": lambda _id, method: "RECISTv1.1 " + method + " TGT_NONTGT_IDN_TXT"
}

labtest_mapping_3 = {
    "patientId": "Subject",
    "testResults": "NEW_LES_APR_IND_2_STD",
    "localId": lambda local_id, *_: local_id,
    "eventType": lambda _id, method: "RECISTv1.1 " + method + " NEW_LES_APR_IND_2_STD"
}

labtest_mapping_4 = {
    "patientId": "Subject",
    "testResults": "TUMOR_SITE_LCTN_NM_STD",
    "localId": lambda local_id, *_: local_id,
    "eventType": lambda _id, method: "RECISTv1.1 " + method + " TUMOR_SITE_LCTN_NM_STD"
}

labtest_mapping_5 = {
    "patientId": "Subject",
    "testResults": "LES_NUM",
    "localId": lambda local_id, *_: local_id,
    "eventType": lambda _id, method: "RECISTv1.1 " + method + " LES_NUM"
}

labtest_mapping_6 = {
    "patientId": "Subject",
    "testResults": "LES_SZ_NUM",
    "localId": lambda local_id, *_: local_id,
    "eventType": lambda _id, method: "RECISTv1.1 " + method + " LES_SZ_NUM"
}

labtest_mapping_7 = {
    "patientId": "Subject",
    "testResults": "MALIGN_SUM_DIAM_VOL",
    "localId": lambda local_id, *_: local_id,
    "eventType": lambda _id, method: "RECISTv1.1 " + method + " MALIGN_SUM_DIAM_VOL"
}

labtest_mapping_8 = {
    "patientId": "Subject",
    "testResults": "TGT_RESP_STD",
    "localId": lambda local_id, *_: local_id,
    "eventType": lambda _id, method: "RECISTv1.1 " + method + " TGT_RESP_STD"
}

labtest_mapping_9 = {
    "patientId": "Subject",
    "testResults": "NTGT_RESP_STD",
    "localId": lambda local_id, *_: local_id,
    "eventType": lambda _id, method: "RECISTv1.1 " + method + " NTGT_RESP_STD"
}

labtest_mapping_10 = {
    "patientId": "Subject",
    "testResults": "OVERALL_LES_RESP_TP_STD",
    "localId": lambda local_id, *_: local_id,
    "eventType": lambda _id, method: "RECISTv1.1 " + method + " OVERALL_LES_RESP_TP_STD"
}

section_to_mapping_types = {
    "demography": [("Patient", patient_mapping_0)],
    "diagnosis": [("Diagnosis", diagnosis_mapping)],
    "survival": [("Outcome", outcome_mapping), ("Patient", patient_mapping_1)],
    "biopsy": [("Sample", sample_mapping_0)],
    "research blood - circulating tumor dna blood": [("Sample", sample_mapping_1)],
    "research blood - normal dna sequence control blood": [("Sample", sample_mapping_1)],
    "research blood - immune assessment for pbmc blood": [("Sample", sample_mapping_1)],
    "course initiation": [("Immunotherapy", immunotherapy_mapping_0)],
    "off treatment": [("Treatment", treatment_mapping_0)],
    "study agent administration": [("Immunotherapy", immunotherapy_mapping_1), ("Treatment", treatment_mapping_1)],
    "adverse events": [],
    "recistv1.1": [("Labtest", labtest_mapping_0), ("Labtest", labtest_mapping_1), ("Labtest", labtest_mapping_2),
                   ("Labtest", labtest_mapping_3), ("Labtest", labtest_mapping_4), ("Labtest", labtest_mapping_5),
                   ("Labtest", labtest_mapping_6), ("Labtest", labtest_mapping_7), ("Labtest", labtest_mapping_8),
                   ("Labtest", labtest_mapping_9), ("Labtest", labtest_mapping_10)]
}

patient_to_id_nums = {}
patient_to_data = {}
dead_patients = set()


def update_dict(row):
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
    section = row["DataPageName"].strip().lower()
    mapping_types = section_to_mapping_types.get(section, [])
    for mapping_type in mapping_types:
        mapping_name = mapping_type[0]
        mapping_dict = mapping_type[1]

        prev_key = None
        new_dict = {}
        for key in mapping_dict:
            if type(mapping_dict[key]) == str:
                new_dict[key] = row[mapping_dict[key]]
            else:  # if the value of the key is of a function type
                args = []
                new_id = section.replace(" ", "_") + "_"
                if section == "recistv1.1":
                    if key == "eventType":
                        method = row["RECIST_MET"]
                        args.append(method)
                    elif key == "localId":
                        new_id += prev_key + "_"

                new_id += str(patient_to_id_nums[patient_id][section])
                args.insert(0, new_id)
                new_dict[key] = mapping_dict[key](*args)
                increment_id_num = True
            prev_key = mapping_dict[key]

        if mapping_name in curr_patient_data:
            if mapping_name == "Patient":
                curr_patient_data[mapping_name] = {**curr_patient_data[mapping_name], **new_dict}
            elif type(curr_patient_data[mapping_name]) == list:
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
    parser = argparse.ArgumentParser()
    parser.add_argument('input-files-dir', help='path to directory containing input files in CSV format')
    parser.add_argument('output-file', help='path to output file in JSON format')
    args = parser.parse_args()

    input_files_dir = getattr(args, 'input-files-dir')
    output_file = getattr(args, 'output-file')

    try:
        input_files = os.listdir(input_files_dir)
    except OSError as e:
        print(f'Error accessing {input_files_dir}: ', e)
        sys.exit(1)

    for input_file in input_files:
        csv_file = None
        try:
            csv_file = open(input_files_dir + input_file)
            reader = csv.DictReader(csv_file)
            for row in reader:
                row = dict(row)
                update_dict(row)

        except OSError as e:
            print(f'Error opening {input_files_dir + input_file}: ', e)
            sys.exit(1)
        finally:
            if csv_file:
                csv_file.close()

    for patient in patient_to_data.keys():
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
                survival_in_months = (death_date - diagnosis_date).days / 30
                patient_to_data[patient]["Outcome"]["overallSurvivalInMonths"] = survival_in_months

    output_dict = {"metadata": list(patient_to_data.values())}
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


if __name__ == '__main__':
    main()
