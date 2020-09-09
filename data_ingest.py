import argparse
import sys
import csv
import json

patient_keys = {
    "patientId",
    "otherIds",
    "dateOfBirth",
    "gender",
    "ethnicity",
    "race",
    "provinceOfResidence",
    "dateOfDeath",
    "causeOfDeath",
    "autopsyTissueForResearch",
    "dateOfPriorMalignancy",
    "familyHistoryAndRiskFactors",
    "familyHistoryOfPredispositionSyndrome"
    "detailsOfPredispositionSyndrome",
    "geneticCancerSyndrome",
    "otherGeneticConditionOrSignificantComorbidity",
    "occupationalOrEnvironmentalExposure",
    "dateOfBirthTier",
    "ethnicityTier",
    "raceTier",
    "dateOfDeathTier",
    "priorMalignancyTier",
    "dateOfPriorMalignancyTier",
    "familyHistoryAndRiskFactorsTier",
    "familyHistoryOfPredispositionSyndromeTier",
    "detailsOfPredispositionSyndromeTier",
    "geneticCancerSyndromeTier",
    "otherGeneticConditionOrSignificantComorbidityTier",
    "causeOfDeathTier",
    "occupationalOrEnvironmentalExposureTier",
    "patientIdTier",
    "otherIdsTier",
    "genderTier",
    "provinceOfResidenceTier",
    "autopsyTissueForResearchTier"
}

enrollment_keys = {
    "patientId",
    "enrollmentInstitution",
    "enrollmentApprovalDate",
    "crossEnrollment",
    "otherPersonalizedMedicineStudyName",
    "otherPersonalizedMedicineStudyId",
    "ageAtEnrollment",
    "eligibilityCategory",
    "statusAtEnrollment",
    "primaryOncologistName",
    "primaryOncologistContact",
    "referringPhysicianName",
    "referringPhysicianContact",
    "summaryOfIdRequest",
    "treatingCentreName",
    "treatingCentreProvince",
    "enrollmentApprovalDateTier",
    "primaryOncologistNameTier",
    "primaryOncologistContactTier",
    "referringPhysicianNameTier",
    "referringPhysicianContactTier",
    "enrollmentInstitutionTier",
    "crossEnrollmentTier",
    "eligibilityCategoryTier",
    "statusAtEnrollmentTier",
    "summaryOfIdRequestTier",
    "treatingCentreNameTier",
    "otherPersonalizedMedicineStudyNameTier",
    "otherPersonalizedMedicineStudyIdTier",
    "patientIdTier",
    "ageAtEnrollmentTier",
    "treatingCentreProvinceTier"
}

consent_keys = {
    "patientId",
    "consentId",
    "consentDate",
    "consentVersion",
    "patientConsentedTo",
    "reasonForRejection",
    "wasAssentObtained",
    "dateOfAssent",
    "assentFormVersion",
    "ifAssentNotObtainedWhyNot",
    "reconsentDate",
    "reconsentVersion",
    "consentingCoordinatorName",
    "previouslyConsented",
    "nameOfOtherBiobank",
    "hasConsentBeenWithdrawn",
    "dateOfConsentWithdrawal",
    "typeOfConsentWithdrawal",
    "reasonForConsentWithdrawal",
    "consentFormComplete",
    "consentDateTier",
    "patientConsentedToTier",
    "reasonForRejectionTier",
    "dateOfAssentTier",
    "reconsentDateTier",
    "consentingCoordinatorNameTier",
    "dateOfConsentWithdrawalTier",
    "typeOfConsentWithdrawalTier",
    "reasonForConsentWithdrawalTier",
    "consentIdTier",
    "wasAssentObtainedTier",
    "assentFormVersionTier",
    "ifAssentNotObtainedWhyNotTier",
    "reconsentVersionTier",
    "previouslyConsentedTier",
    "hasConsentBeenWithdrawnTier",
    "consentVersionTier",
    "nameOfOtherBiobankTier",
    "consentFormCompleteTier",
    "patientIdTier"
}

diagnosis_keys = {
    "patientId",
    "diagnosisId",
    "diagnosisDate",
    "ageAtDiagnosis",
    "cancerType",
    "classification",
    "cancerSite",
    "histology",
    "methodOfDefinitiveDiagnosis",
    "sampleType",
    "sampleSite",
    "tumorGrade",
    "gradingSystemUsed",
    "sitesOfMetastases",
    "stagingSystem",
    "versionOrEditionOfTheStagingSystem",
    "specificTumorStageAtDiagnosis",
    "prognosticBiomarkers",
    "biomarkerQuantification",
    "additionalMolecularTesting",
    "additionalTestType",
    "laboratoryName",
    "laboratoryAddress",
    "siteOfMetastases",
    "stagingSystemVersion",
    "specificStage",
    "cancerSpecificBiomarkers",
    "additionalMolecularDiagnosticTestingPerformed",
    "additionalTest",
    "laboratoryAddressTier",
    "gradingSystemUsedTier",
    "stagingSystemTier",
    "prognosticBiomarkersTier",
    "biomarkerQuantificationTier",
    "additionalMolecularTestingTier",
    "additionalTestTypeTier",
    "laboratoryNameTier",
    "stagingSystemVersionTier",
    "specificStageTier",
    "cancerSpecificBiomarkersTier",
    "additionalMolecularDiagnosticTestingPerformedTier",
    "additionalTestTier",
    "diagnosisDateTier",
    "ageAtDiagnosisTier",
    "tumorGradeTier",
    "specificTumorStageAtDiagnosisTier",
    "siteOfMetastasesTier",
    "patientIdTier",
    "diagnosisIdTier",
    "cancerTypeTier",
    "classificationTier",
    "cancerSiteTier",
    "histologyTier",
    "methodOfDefinitiveDiagnosisTier",
    "sampleTypeTier",
    "sampleSiteTier",
    "sitesOfMetastasesTier",
    "versionOrEditionOfTheStagingSystemTier"
}

sample_keys = {
    "patientId",
    "sampleId",
    "diagnosisId",
    "localBiobankId",
    "collectionDate",
    "collectionHospital",
    "sampleType",
    "tissueDiseaseState",
    "anatomicSiteTheSampleObtainedFrom",
    "cancerType",
    "cancerSubtype",
    "pathologyReportId",
    "morphologicalCode",
    "topologicalCode",
    "shippingDate",
    "receivedDate",
    "qualityControlPerformed",
    "estimatedTumorContent",
    "quantity",
    "units",
    "associatedBiobank",
    "otherBiobank",
    "sopFollowed",
    "ifNotExplainAnyDeviation",
    "pathologyReportIdTier",
    "shippingDateTier",
    "receivedDateTier",
    "collectionDateTier",
    "tissueDiseaseStateTier",
    "quantityTier",
    "unitsTier",
    "otherBiobankTier",
    "ifNotExplainAnyDeviationTier",
    "collectionHospitalTier",
    "sampleTypeTier",
    "anatomicSiteTheSampleObtainedFromTier",
    "qualityControlPerformedTier",
    "associatedBiobankTier",
    "sopFollowedTier",
    "patientIdTier",
    "sampleIdTier",
    "diagnosisIdTier",
    "localBiobankIdTier",
    "cancerTypeTier",
    "cancerSubtypeTier",
    "morphologicalCodeTier",
    "topologicalCodeTier",
    "estimatedTumorContentTier",
    "recordingDateTier",
    "startIntervalTier"
}

treatment_keys = {
    "patientId",
    "courseNumber",
    "therapeuticModality",
    "treatmentPlanType",
    "treatmentIntent",
    "startDate",
    "stopDate",
    "reasonForEndingTheTreatment",
    "responseToTreatment",
    "dateOfRecurrenceOrProgressionAfterThisTreatment",
    "unexpectedOrUnusualToxicityDuringTreatment",
    "diagnosisId",
    "treatmentPlanId",
    "responseCriteriaUsed",
    "treatmentPlanTypeTier",
    "treatmentIntentTier",
    "reasonForEndingTheTreatmentTier",
    "surgeryDetailsTier",
    "responseCriteriaUsedTier",
    "courseNumberTier",
    "therapeuticModalityTier",
    "systematicTherapyAgentNameTier",
    "startDateTier",
    "stopDateTier",
    "responseToTreatmentTier",
    "dateOfRecurrenceOrProgressionAfterThisTreatmentTier",
    "unexpectedOrUnusualToxicityDuringTreatmentTier",
    "patientIdTier"
}

outcome_keys = {
    "patientId",
    "physicalExamId",
    "dateOfAssessment",
    "diseaseResponseOrStatus",
    "otherResponseClassification",
    "minimalResidualDiseaseAssessment",
    "methodOfResponseEvaluation",
    "responseCriteriaUsed",
    "summaryStage",
    "sitesOfAnyProgressionOrRecurrence",
    "vitalStatus",
    "height",
    "weight",
    "heightUnits",
    "weightUnits",
    "performanceStatus",
    "dateOfAssessmentTier",
    "otherResponseClassificationTier",
    "minimalResidualDiseaseAssessmentTier",
    "methodOfResponseEvaluationTier",
    "responseCriteriaUsedTier",
    "summaryStageTier",
    "sitesOfAnyProgressionOrRecurrenceTier",
    "vitalStatusTier",
    "diseaseResponseOrStatusTier",
    "heightTier",
    "weightTier",
    "heightUnitsTier",
    "weightUnitsTier",
    "performanceStatusTier",
    "patientIdTier",
    "physicalExamIdTier",
    "overallSurvivalInMonthsTier",
    "diseaseFreeSurvivalInMonthsTier"
}

complication_keys = {
    "patientId",
    "date",
    "lateComplicationOfTherapyDeveloped",
    "lateToxicityDetail",
    "suspectedTreatmentInducedNeoplasmDeveloped",
    "treatmentInducedNeoplasmDetails",
    "suspectedTreatmentInducedNeoplasmDevelopedTier",
    "treatmentInducedNeoplasmDetailsTier",
    "dateTier",
    "lateComplicationOfTherapyDevelopedTier",
    "lateToxicityDetailTier",
    "patientIdTier"
}

tumourboard_keys = {
    "patientId",
    "dateOfMolecularTumorBoard",
    "typeOfSampleAnalyzed",
    "typeOfTumourSampleAnalyzed",
    "analysesDiscussed",
    "somaticSampleType",
    "normalExpressionComparator",
    "diseaseExpressionComparator",
    "hasAGermlineVariantBeenIdentifiedByProfilingThatMayPredisposeToCancer",
    "actionableTargetFound",
    "molecularTumorBoardRecommendation",
    "germlineDnaSampleId",
    "tumorDnaSampleId",
    "tumorRnaSampleId",
    "germlineSnvDiscussed",
    "somaticSnvDiscussed",
    "cnvsDiscussed",
    "structuralVariantDiscussed",
    "classificationOfVariants",
    "clinicalValidationProgress",
    "typeOfValidation",
    "agentOrDrugClass",
    "levelOfEvidenceForExpressionTargetAgentMatch",
    "didTreatmentPlanChangeBasedOnProfilingResult",
    "howTreatmentHasAlteredBasedOnProfiling",
    "reasonTreatmentPlanDidNotChangeBasedOnProfiling",
    "detailsOfTreatmentPlanImpact",
    "patientOrFamilyInformedOfGermlineVariant",
    "patientHasBeenReferredToAHereditaryCancerProgramBasedOnThisMolecularProfiling",
    "summaryReport",
    "dateOfMolecularTumorBoardTier",
    "summaryReportTier",
    "typeOfSampleAnalyzedTier",
    "typeOfTumourSampleAnalyzedTier",
    "analysesDiscussedTier",
    "somaticSampleTypeTier",
    "normalExpressionComparatorTier",
    "diseaseExpressionComparatorTier",
    "hasAGermlineVariantBeenIdentifiedByProfilingThatMayPredisposeToCancerTier",
    "actionableTargetFoundTier",
    "molecularTumorBoardRecommendationTier",
    "germlineDnaSampleIdTier",
    "tumorDnaSampleIdTier",
    "tumorRnaSampleIdTier",
    "germlineSnvDiscussedTier",
    "somaticSnvDiscussedTier",
    "cnvsDiscussedTier",
    "structuralVariantDiscussedTier",
    "classificationOfVariantsTier",
    "clinicalValidationProgressTier",
    "typeOfValidationTier",
    "agentOrDrugClassTier",
    "levelOfEvidenceForExpressionTargetAgentMatchTier",
    "didTreatmentPlanChangeBasedOnProfilingResultTier",
    "howTreatmentHasAlteredBasedOnProfilingTier",
    "reasonTreatmentPlanDidNotChangeBasedOnProfilingTier",
    "detailsOfTreatmentPlanImpactTier",
    "patientOrFamilyInformedOfGermlineVariantTier",
    "patientHasBeenReferredToAHereditaryCancerProgramBasedOnThisMolecularProfilingTier",
    "patientIdTier"
}

chemotherapy_keys = {
    "patientId",
    "courseNumber",
    "startDate",
    "stopDate",
    "systematicTherapyAgentName",
    "route",
    "dose",
    "doseUnit",
    "doseFrequency",
    "daysPerCycle",
    "numberOfCycle",
    "treatmentIntent",
    "treatingCentreName",
    "type",
    "protocolCode",
    "recordingDate",
    "treatmentPlanId",
    "patientIdTier",
    "courseNumberTier",
    "startDateTier",
    "stopDateTier",
    "systematicTherapyAgentNameTier",
    "routeTier",
    "doseTier",
    "doseFrequencyTier",
    "doseUnitTier",
    "daysPerCycleTier",
    "numberOfCycleTier",
    "treatmentIntentTier",
    "treatingCentreNameTier",
    "typeTier",
    "protocolCodeTier",
    "recordingDateTier",
    "treatmentPlanIdTier"
}

slide_keys = {
    "patientId",
    "sampleId",
    "slideId",
    "slideOtherId",
    "lymphocyteInfiltrationPercent",
    "monocyteInfiltrationPercent",
    "normalCellsPercent",
    "tumorCellsPercent",
    "stromalCellsPercent",
    "eosinophilInfiltrationPercent",
    "neutrophilInfiltrationPercent",
    "granulocyteInfiltrationPercent",
    "necrosisPercent",
    "inflammatoryInfiltrationPercent",
    "proliferatingCellsNumber",
    "sectionLocation",
    "tumorNucleiPercent",
    "patientIdTier",
    "sampleIdTier",
    "slideIdTier",
    "slideOtherIdTier",
    "lymphocyteInfiltrationPercentTier",
    "tumorNucleiPercentTier",
    "monocyteInfiltrationPercentTier",
    "normalCellsPercentTier",
    "tumorCellsPercentTier",
    "stromalCellsPercentTier",
    "eosinophilInfiltrationPercentTier",
    "neutrophilInfiltrationPercentTier",
    "granulocyteInfiltrationPercentTier",
    "necrosisPercentTier",
    "inflammatoryInfiltrationPercentTier",
    "proliferatingCellsNumberTier",
    "sectionLocationTier"
}

study_keys = {
    "patientId",
    "startDate",
    "endDate",
    "status",
    "recordingDate",
    "patientIdTier",
    "startDateTier",
    "endDateTier",
    "statusTier",
    "recordingDateTier"
}

labtest_keys = {
    "patientId",
    "startDate",
    "collectionDate",
    "endDate",
    "eventType",
    "testResults",
    "timePoint",
    "recordingDate",
    "patientIdTier",
    "startDateTier",
    "collectionDateTier",
    "endDateTier",
    "eventTypeTier",
    "testResultsTier",
    "timePointTier",
    "recordingDateTier"
}


def get_dict(keys, mapping, tier_values, row):
    return_dict = dict.fromkeys(keys, "")
    for key in return_dict:
        if key in mapping:
            return_dict[key] = row[mapping[key]]
        elif key in tier_values:
            return_dict[key] = tier_values[key]

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
                    "Patient": get_dict(patient_keys, row),
                    "Enrollment": get_dict(enrollment_keys, row),
                    "Consent": get_dict(consent_keys, row),
                    "Diagnosis": get_dict(diagnosis_keys, row),
                    "Sample": get_dict(sample_keys, row),
                    "Treatment": get_dict(treatment_keys, row),
                    "Outcome": get_dict(outcome_keys, row),
                    "Complication": get_dict(complication_keys, row),
                    "Tumourboard": get_dict(tumourboard_keys, row),
                    "Chemotherapy": get_dict(chemotherapy_keys, row),
                    "Slide": get_dict(slide_keys, row),
                    "Study": get_dict(study_keys, row),
                    "Labtest": get_dict(labtest_keys, row)
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
