#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validate.py - Validates a batch ingest or update datafile for clinical and pipeline tables.

Usage:
  validate [-h Help] [-v Version] [-d Description] [--overwrite] [-p LoggingPath] <metadata_json>

Options:
  -h --help        Show this screen.
  -v --version     Version.
  -d <description> A text description of the dataset to be created.
  --overwrite      If this flag is specified, existing records will be overwritten.
  -p LoggingPath   Path to directory where the logs will be saved.
  <metadata_json>  Path to the json file that contains clinical and pipeline data.

"""

import json
import os
import re
from docopt import docopt

from candig.ingest_logging import logging
import candig.ingest._version as version

import candig.server.datarepo as repo
import candig.server.exceptions as exceptions

from candig.server.datamodel.datasets import Dataset
from candig.server.datamodel.bio_metadata import Individual
from candig.server.datamodel.bio_metadata import Biosample
from candig.server.datamodel.clinical_metadata import Patient
from candig.server.datamodel.clinical_metadata import Enrollment
from candig.server.datamodel.clinical_metadata import Consent
from candig.server.datamodel.clinical_metadata import Diagnosis
from candig.server.datamodel.clinical_metadata import Sample
from candig.server.datamodel.clinical_metadata import Treatment
from candig.server.datamodel.clinical_metadata import Outcome
from candig.server.datamodel.clinical_metadata import Complication
from candig.server.datamodel.clinical_metadata import Tumourboard
from candig.server.datamodel.clinical_metadata import Chemotherapy
from candig.server.datamodel.clinical_metadata import Radiotherapy
from candig.server.datamodel.clinical_metadata import Immunotherapy
from candig.server.datamodel.clinical_metadata import Surgery
from candig.server.datamodel.clinical_metadata import Celltransplant
from candig.server.datamodel.clinical_metadata import Slide
from candig.server.datamodel.clinical_metadata import Study
from candig.server.datamodel.clinical_metadata import Labtest
from candig.server.datamodel.bio_metadata import Experiment
from candig.server.datamodel.bio_metadata import Analysis
from candig.server.datamodel.pipeline_metadata import Extraction
from candig.server.datamodel.pipeline_metadata import Sequencing
from candig.server.datamodel.pipeline_metadata import Alignment
from candig.server.datamodel.pipeline_metadata import VariantCalling
from candig.server.datamodel.pipeline_metadata import FusionDetection
from candig.server.datamodel.pipeline_metadata import ExpressionAnalysis


class CandigRepo(object):
    """
    Handles the interaction with the database repo.
    
    """
    def __init__(self, filename):
        """
        Parameters
        ==========
        filename: string
            Filename and path information of the repository.

        """
        self._filename = filename
        self._repo = None

        self.clinical_metadata_map = {
            'Patient': {
                'table': Patient,
                'local_id': ['patientId'],
                'repo_add': self.add_patient,
                'repo_update': self.update_patient
            },
            'Enrollment': {
                'table': Enrollment,
                'local_id': ["patientId", "enrollmentApprovalDate"],
                'repo_add': self.add_enrollment,
                'repo_update': self.update_enrollment
            },
            'Consent': {
                'table': Consent,
                'local_id': ["patientId", "consentDate"],
                'repo_add': self.add_consent,
                'repo_update': self.update_consent
            },
            'Diagnosis': {
                'table': Diagnosis,
                'local_id': ["patientId", "diagnosisDate"],
                'repo_add': self.add_diagnosis,
                'repo_update': self.update_diagnosis
            },
            'Sample': {
                'table': Sample,
                'local_id': ["patientId", "sampleId"],
                'repo_add': self.add_sample,
                'repo_update': self.update_sample
            },
            'Treatment': {
                'table': Treatment,
                'local_id': ["patientId", "startDate"],
                'repo_add': self.add_treatment,
                'repo_update': self.update_treatment
            },
            'Outcome': {
                'table': Outcome,
                'local_id': ["patientId", "dateOfAssessment"],
                'repo_add': self.add_outcome,
                'repo_update': self.update_outcome
            },
            'Complication': {
                'table': Complication,
                'local_id': ["patientId", "date"],
                'repo_add': self.add_complication,
                'repo_update': self.update_complication
            },
            'Tumourboard': {
                'table': Tumourboard,
                'local_id': ["patientId", "dateOfMolecularTumorBoard"],
                'repo_add': self.add_tumourboard,
                'repo_update': self.update_tumourboard
            },
            'Chemotherapy': {
                'table': Chemotherapy,
                'local_id': ["patientId", "treatmentPlanId", "systematicTherapyAgentName"],
                'repo_add': self.add_chemotherapy,
                'repo_update': self.update_chemotherapy
            },
            'Radiotherapy': {
                'table': Radiotherapy,
                'local_id': ["patientId", "courseNumber", "treatmentPlanId", "startDate"],
                'repo_add': self.add_radiotherapy,
                'repo_update': self.update_radiotherapy
            },
            'Immunotherapy': {
                'table': Immunotherapy,
                'local_id': ["patientId", "treatmentPlanId", "startDate"],
                'repo_add': self.add_immunotherapy,
                'repo_update': self.update_immunotherapy
            },
            'Surgery': {
                'table': Surgery,
                'local_id': ["patientId", "treatmentPlanId", "startDate", "sampleId"],
                'repo_add': self.add_surgery,
                'repo_update': self.update_surgery
            },
            'Celltransplant': {
                'table': Celltransplant,
                'local_id': ["patientId", "treatmentPlanId", "startDate"],
                'repo_add': self.add_celltransplant,
                'repo_update': self.update_celltransplant
            },
            'Slide': {
                'table': Slide,
                'local_id': ["patientId", "slideId"],
                'repo_add': self.add_slide,
                'repo_update': self.update_slide
            },
            'Study': {
                'table': Study,
                'local_id': ["patientId", "startDate"],
                'repo_add': self.add_study,
                'repo_update': self.update_study
            },
            'Labtest': {
                'table': Labtest,
                'local_id': ["patientId", "startDate"],
                'repo_add': self.add_labtest,
                'repo_update': self.update_labtest
            }
        }
        self.pipeline_metadata_map = {
            'Extraction': {
                'table': Extraction,
                'local_id': ["sampleId", "extractionId"],
                'repo_add': self.add_extraction,
                'repo_update': self.update_extraction
            },
            'Sequencing': {
                'table': Sequencing,
                'local_id': ["sampleId", "sequencingId"],
                'repo_add': self.add_sequencing,
                'repo_update': self.update_sequencing
            },
            'Alignment': {
                'table': Alignment,
                'local_id': ["sampleId", "alignmentId"],
                'repo_add': self.add_alignment,
                'repo_update': self.update_alignment
            },
            'VariantCalling': {
                'table': VariantCalling,
                'local_id': ["sampleId", "variantCallingId"],
                'repo_add': self.add_variant_calling,
                'repo_update': self.update_variant_calling
            },
            'FusionDetection': {
                'table': FusionDetection,
                'local_id': ["sampleId", "fusionDetectionId"],
                'repo_add': self.add_fusion_detection,
                'repo_update': self.update_fusion_detection
            },
            'ExpressionAnalysis': {
                'table': ExpressionAnalysis,
                'local_id': ["sampleId", "expressionAnalysisId"],
                'repo_add': self.add_expression_analysis,
                'repo_update': self.update_expression_analysis
            }
        }

    def __enter__(self):
        self._repo = repo.SqlDataRepository(self._filename)
        self._repo.open(repo.MODE_WRITE)

        if not os.path.isfile(self._filename):
            self._repo.initialise()

        return self

    def __exit__(self, extype, value, traceback):
        self._repo.commit()
        self._repo.verify()
        self._repo.close()
        self._repo.delete()

    def _commit_record(self):
        self._repo.commit()
        self._repo.verify()

    def add_dataset(self, dataset):
        self._repo.insertDataset(dataset)
        self._commit_record()

    def add_patient(self, patient):
        self._repo.insertPatient(patient)
        self._commit_record()

    def add_enrollment(self, enrollment):
        self._repo.insertEnrollment(enrollment)
        self._commit_record()

    def add_consent(self, consent):
        self._repo.insertConsent(consent)
        self._commit_record()

    def add_diagnosis(self, diagnosis):
        self._repo.insertDiagnosis(diagnosis)
        self._commit_record()

    def add_sample(self, sample):
        self._repo.insertSample(sample)
        self._commit_record()

    def add_treatment(self, treatment):
        self._repo.insertTreatment(treatment)
        self._commit_record()

    def add_outcome(self, outcome):
        self._repo.insertOutcome(outcome)
        self._commit_record()

    def add_complication(self, complication):
        self._repo.insertComplication(complication)
        self._commit_record()

    def add_tumourboard(self, tumourboard):
        self._repo.insertTumourboard(tumourboard)
        self._commit_record()

    def add_chemotherapy(self, chemotherapy):
        self._repo.insertChemotherapy(chemotherapy)
        self._commit_record()

    def add_radiotherapy(self, radiotherapy):
        self._repo.insertRadiotherapy(radiotherapy)
        self._commit_record()

    def add_immunotherapy(self, immunotherapy):
        self._repo.insertImmunotherapy(immunotherapy)
        self._commit_record()

    def add_surgery(self, surgery):
        self._repo.insertSurgery(surgery)
        self._commit_record()

    def add_celltransplant(self, celltransplant):
        self._repo.insertCelltransplant(celltransplant)
        self._commit_record()

    def add_slide(self, slide):
        self._repo.insertSlide(slide)
        self._commit_record()

    def add_study(self, study):
        self._repo.insertStudy(study)
        self._commit_record()

    def add_labtest(self, labtest):
        self._repo.insertLabtest(labtest)
        self._commit_record()

    def add_extraction(self, extraction):
        self._repo.insertExtraction(extraction)
        self._commit_record()

    def add_sequencing(self, sequencing):
        self._repo.insertSequencing(sequencing)
        self._commit_record()

    def add_alignment(self, alignment):
        self._repo.insertAlignment(alignment)
        self._commit_record()

    def add_variant_calling(self, variant_calling):
        self._repo.insertVariantCalling(variant_calling)
        self._commit_record()

    def add_fusion_detection(self, fusion_detection):
        self._repo.insertFusionDetection(fusion_detection)
        self._commit_record()

    def add_expression_analysis(self, expression_analysis):
        self._repo.insertExpressionAnalysis(expression_analysis)
        self._commit_record()

    def update_patient(self, patient):
        self._repo.removePatient(patient)
        self._repo.insertPatient(patient)
        self._commit_record()

    def update_enrollment(self, enrollment):
        self._repo.removeEnrollment(enrollment)
        self._repo.insertEnrollment(enrollment)
        self._commit_record()

    def update_consent(self, consent):
        self._repo.removeConsent(consent)
        self._repo.insertConsent(consent)
        self._commit_record()

    def update_diagnosis(self, diagnosis):
        self._repo.removeDiagnosis(diagnosis)
        self._repo.insertDiagnosis(diagnosis)
        self._commit_record()

    def update_sample(self, sample):
        self._repo.removeSample(sample)
        self._repo.insertSample(sample)
        self._commit_record()

    def update_treatment(self, treatment):
        self._repo.removeTreatment(treatment)
        self._repo.insertTreatment(treatment)
        self._commit_record()

    def update_outcome(self, outcome):
        self._repo.removeOutcome(outcome)
        self._repo.insertOutcome(outcome)
        self._commit_record()

    def update_complication(self, complication):
        self._repo.removeComplication(complication)
        self._repo.insertComplication(complication)
        self._commit_record()

    def update_tumourboard(self, tumourboard):
        self._repo.removeTumourboard(tumourboard)
        self._repo.insertTumourboard(tumourboard)
        self._commit_record()

    def update_chemotherapy(self, chemotherapy):
        self._repo.removeChemotherapy(chemotherapy)
        self._repo.insertChemotherapy(chemotherapy)
        self._commit_record()

    def update_radiotherapy(self, radiotherapy):
        self._repo.removeRadiotherapy(radiotherapy)
        self._repo.insertRadiotherapy(radiotherapy)
        self._commit_record()

    def update_immunotherapy(self, immunotherapy):
        self._repo.removeImmunotherapy(immunotherapy)
        self._repo.insertImmunotherapy(immunotherapy)
        self._commit_record()

    def update_surgery(self, surgery):
        self._repo.removeSurgery(surgery)
        self._repo.insertSurgery(surgery)
        self._commit_record()

    def update_celltransplant(self, celltransplant):
        self._repo.removeCelltransplant(celltransplant)
        self._repo.insertCelltransplant(celltransplant)
        self._commit_record()

    def update_slide(self, slide):
        self._repo.removeSlide(slide)
        self._repo.insertSlide(slide)
        self._commit_record()

    def update_study(self, study):
        self._repo.removeStudy(study)
        self._repo.insertStudy(study)
        self._commit_record()

    def update_labtest(self, labtest):
        self._repo.removeLabtest(labtest)
        self._repo.insertLabtest(labtest)
        self._commit_record()

    def update_extraction(self, extraction):
        self._repo.removeExtraction(extraction)
        self._repo.insertExtraction(extraction)
        self._commit_record()

    def update_sequencing(self, sequencing):
        self._repo.removeSequencing(sequencing)
        self._repo.insertSequencing(sequencing)
        self._commit_record()

    def update_alignment(self, alignment):
        self._repo.removeAlignment(alignment)
        self._repo.insertAlignment(alignment)
        self._commit_record()

    def update_variant_calling(self, variant_calling):
        self._repo.removeVariantCalling(variant_calling)
        self._repo.insertVariantCalling(variant_calling)
        self._commit_record()

    def update_fusion_detection(self, fusion_detection):
        self._repo.removeFusionDetection(fusion_detection)
        self._repo.insertFusionDetection(fusion_detection)
        self._commit_record()

    def update_expression_analysis(self, expression_analysis):
        self._repo.removeExpressionAnalysis(expression_analysis)
        self._repo.insertExpressionAnalysis(expression_analysis)
        self._commit_record()

def main():
    """
    """
    # Parse arguments
    args = docopt(__doc__, version='ingest ' + str(version.version))
    path_to_database = '/tmp/repo.db'
    dataset_name = 'validate_me'
    metadata_json = args['<metadata_json>']
    dataset_description = args.get('-d')
    logging_path = args.get('-p')

    logger = logging.getLogger(path=logging_path)

    objects_count = 0

    # Read and parse profyle metadata json
    with open(metadata_json, 'r') as json_datafile:
        metadata = json.load(json_datafile)
    
    old_metadata = json.dumps(metadata, indent=2)

    # Create a dataset
    dataset = Dataset(dataset_name)
    dataset.setDescription(dataset_description)

    # Open and load the data
    with CandigRepo(path_to_database) as repo:

        with repo._repo.database.transaction():
            # Add dataset
            try:
                repo.add_dataset(dataset)
            except exceptions.DuplicateNameException:
                pass

            metadata_map = {
                'metadata': repo.clinical_metadata_map,
                'pipeline_metadata': repo.pipeline_metadata_map
            }

            metadata_key = list(metadata.keys())[0]

            # Iterate through metadata file type based on key and update the dataset
            for individual in metadata[metadata_key]:
                patientId = individual['Patient']['patientId']
                logger.info(f'Looking at individual {patientId}...')
                for table in individual:
                    if table in metadata_map[metadata_key]:

                        records = individual[table]
                        if type(records) == dict:
                            records = [records]

                        for record in records:
                            # Validate that any present patientID is the same as the main one
                            if 'patientId' not in record:
                              record['patientId'] = patientId
                            if record.get('patientId') != patientId:
                              this_patientId = record.get('patientId')
                              logger.info(f'PatientId in table "{table}" is "{this_patientId}", not {patientId}')
                            # If localId is present, use it as the localId
                            # Otherwise, attempt to contruct localId from predetermined fields
                            if record.get('localId') and table in ['Patient', 'Sample']:
                                logger.info('localId should not be specified for the', table, 'table.')

                            if record.get('localId') and table not in ['Patient', 'Sample']:
                                local_id = record.get('localId')

                            else:
                                local_id_list = []
                                for x in metadata_map[metadata_key][table]['local_id']:
                                    if record.get(x):
                                        local_id_list.append(record[x])
                                    else:
                                        logger.info("Skipped: Missing 1 or more primary identifiers for record in: {0} needs {1}, received {2}".format(
                                            table,
                                            metadata_map[metadata_key][table]['local_id'],
                                            local_id_list,
                                            ))
                                        if table not in ['Patient', 'Sample']:
                                            logger.info("You may also specify localId to uniquely denote records.")
                                        local_id_list = None
                                        break
                                if not local_id_list:
                                    continue

                                local_id = "_".join(local_id_list)

                            obj = metadata_map[metadata_key][table]['table'](dataset, localId=local_id)
                            
                            # Check to see if the record has any keys that are not proper attribute names
                            for key in record:
                              if key == 'localId':
                                continue
                              try:
                                obj.mapper(key)
                              except exceptions.BadFieldNameException as e:
                                nameMatch = re.match(r'(.+) is not a valid field name, are you looking for (.+)\?', e.message)
                                record[nameMatch.group(2)] = record.pop(nameMatch.group(1))
                                logger.info(f'Rename "{nameMatch.group(1)}" to "{nameMatch.group(2)}"')
                              except Exception as e:
                                logger.info(e)
                            repo_obj = obj.populateFromJson(json.dumps(record))

                            # Add object into the repo file
                            try:
                                metadata_map[metadata_key][table]['repo_add'](repo_obj)
                                objects_count += 1
                            except exceptions.DuplicateNameException:
                                if args['--overwrite']:
                                    metadata_map[metadata_key][table]['repo_update'](repo_obj)
                                    logger.info("Overwriting record for local identifier {} at {} table".format(
                                        local_id, table))
                                else:
                                    logger.info("Skipped: Duplicate {0} record name detected: {1} ".format(
                                        table, local_id))
                            except Exception as e:
                                logger.info(e.message)

    logger.info("{} objects have been processed.".format(objects_count))
    
    new_metadata = json.dumps(metadata, indent=2)
    if old_metadata != new_metadata:
      logger.info(f'There are suggested changes for your datafile in {metadata_json}.new')
      with open(f'{metadata_json}.new', 'w') as json_datafile:
        json_datafile.write(new_metadata)
    return None

if __name__ == "__main__":
    main()
