import csv
from celery import Celery
from API import validators as validators
from Core import models as core_models
from MasterData import models as master_data_models
import os
from django.http import HttpResponse
import datetime

app = Celery()


@app.task
def save_payload_from_csv(request):
    root_path = "uploads"
    i = 0
    for subdir, _, _ in os.walk(root_path):
        for file in os.listdir(subdir):
            file_path = "" + root_path + "/" + file
            with open(file_path, 'r') as fp:
                lines = csv.reader(fp, delimiter=',')

                for line in lines:
                    if i == 1:
                        message_type = line[2]
                        facility_hfr_code = line[3]
                        facility_name = line[4]

                        print(message_type)
                        # Service received parents lines
                        if message_type == "SVCREC":
                            instance_service_received = core_models.ServiceReceived()
                            instance_service_received.org_name = facility_name
                            instance_service_received.facility_hfr_code = facility_hfr_code
                            instance_service_received.save()

                            # Death by Facility in facility parent lines
                        if message_type == "DDC":
                            instance_death_by_disease_case_at_facility = core_models.DeathByDiseaseCaseAtFacility()
                            instance_death_by_disease_case_at_facility.org_name = facility_name
                            instance_death_by_disease_case_at_facility.facility_hfr_code = facility_hfr_code
                            instance_death_by_disease_case_at_facility.save()

                            # Death by Disease Case Out of Faciity lines
                        if message_type == "DDCOUT":
                            instance_death_by_disease_case_not_at_facility = core_models.DeathByDiseaseCaseNotAtFacility()
                            instance_death_by_disease_case_not_at_facility.org_name = facility_name
                            instance_death_by_disease_case_not_at_facility.facility_hfr_code = facility_hfr_code
                            instance_death_by_disease_case_not_at_facility.save()
                            # Bed Occupany parent lines

                        if message_type == "BEDOCC":
                            instance_bed_occupancy = core_models.BedOccupancy()
                            instance_bed_occupancy.org_name = facility_name
                            instance_bed_occupancy.facility_hfr_code = facility_hfr_code
                            instance_bed_occupancy.save()

                            # Revenue received parent lines
                        if message_type == "REV":
                            instance_revenue_received = core_models.RevenueReceived()
                            instance_revenue_received.org_name = facility_name
                            instance_revenue_received.facility_hfr_code = facility_hfr_code
                            instance_revenue_received.save()

                    i += 1

                for line in lines:
                    row = 0

                    if row == 0:
                        headers = line
                        row = row + 1
                    else:
                        # create a dictionary of student details
                        transaction_id = line[1]

                        new_line_details = {}
                        for i in range(len(headers)):
                            new_line_details[headers[i]] = line[i]

                        # save the transaction lines and message
                        if message_type == "SVCREC":
                            transaction_id = line[1]

                            instance_service_received_items = core_models.ServiceReceivedItems()
                            instance_service_received_items.service_received_id = instance_service_received.id
                            instance_service_received_items.department_name = line[4]
                            instance_service_received_items.department_id = line[5]
                            instance_service_received_items.patient_id = line[6]
                            instance_service_received_items.gender = line[7]
                            instance_service_received_items.date_of_birth = validators.convert_date_formats(line[8])
                            instance_service_received_items.med_svc_code = line[9]
                            instance_service_received_items.icd_10_code = line[10]
                            instance_service_received_items.service_date = validators.convert_date_formats(line[11])
                            instance_service_received_items.service_provider_ranking_id = line[12]
                            instance_service_received_items.visit_type = line[13]
                            instance_service_received_items.save()

                            # Update transactions
                            update_transaction_summary(transaction_id)

                        elif message_type == "DDC":
                            instance_death_by_disease_case_items = core_models.DeathByDiseaseCaseAtFacility()

                            instance_death_by_disease_case_items.death_by_disease_case_at_facility_id = instance_death_by_disease_case_at_facility.id
                            instance_death_by_disease_case_items.ward_name = line[5]
                            instance_death_by_disease_case_items.ward_id = line[4]
                            instance_death_by_disease_case_items.patient_id = line[6]
                            instance_death_by_disease_case_items.icd_10_code = line[7]
                            instance_death_by_disease_case_items.gender = line[8]
                            instance_death_by_disease_case_items.date_of_birth = line[9]
                            instance_death_by_disease_case_items.date_death_occurred = line[10]
                            instance_death_by_disease_case_items.save()

                            update_transaction_summary(transaction_id)

                        elif message_type == "DDCOUT":
                            instance_death_by_disease_case_items_not_at_facility = core_models.DeathByDiseaseCaseNotAtFacilityItems()

                            instance_death_by_disease_case_items_not_at_facility.death_by_disease_case_not_at_facility_id = instance_death_by_disease_case_not_at_facility.id
                            instance_death_by_disease_case_items_not_at_facility.place_of_death_id = line[5]
                            instance_death_by_disease_case_items_not_at_facility.gender = line[4]
                            instance_death_by_disease_case_items_not_at_facility.date_of_birth = line[6]
                            instance_death_by_disease_case_items_not_at_facility.icd_10_code = line[7]
                            instance_death_by_disease_case_items_not_at_facility.date_death_occurred = line[8]
                            instance_death_by_disease_case_items_not_at_facility.death_id = line[9]
                            instance_death_by_disease_case_items_not_at_facility.save()

                            update_transaction_summary(transaction_id)

                        elif message_type == "BEDOCC":
                            instance_bed_occupancy_items = core_models.BedOccupancyItems()

                            instance_bed_occupancy_items.bed_occupancy_id = instance_bed_occupancy.id
                            instance_bed_occupancy_items.patient_id = line(6)
                            instance_bed_occupancy_items.admission_date = line[7]
                            instance_bed_occupancy_items.discharge_date = line[8]
                            instance_bed_occupancy_items.ward_name = line[5]
                            instance_bed_occupancy_items.ward_id = line[4]
                            instance_bed_occupancy_items.save()

                            update_transaction_summary(transaction_id)

                        elif message_type == "REV":
                            instance_revenue_received_items = core_models.RevenueReceivedItems()

                            instance_revenue_received_items.revenue_received_id = instance_revenue_received.id
                            instance_revenue_received_items.system_trans_id = line(4)
                            instance_revenue_received_items.transaction_date = line(5)
                            instance_revenue_received_items.patient_id = line[6]
                            instance_revenue_received_items.gender = line[7]
                            instance_revenue_received_items.date_of_birth = line[8]
                            instance_revenue_received_items.med_svc_code = line[9]
                            instance_revenue_received_items.payer_id = line[10]
                            instance_revenue_received_items.exemption_category_id = line[11]
                            instance_revenue_received_items.billed_amount = line[12]
                            instance_revenue_received_items.waived_amount = line[13]
                            instance_revenue_received_items.service_provider_ranking_id = line[14]
                            instance_revenue_received_items.save()

                            update_transaction_summary(transaction_id)

                        else:
                            return False
                    row = row + 1

                i = 0
                fp.close()

        return HttpResponse(".")


def update_transaction_summary(transaction_id):
    transaction = core_models.TransactionSummary.objects.get(id=transaction_id)
    transaction.total_passed += 1
    transaction.total_failed -= 1
    transaction.save()


@app.task
def calculate_and_save_bed_occupancy_rate(bed_occupancy_id):
    bed_occupancy = core_models.BedOccupancy.objects.filter(admission_date__gte=datetime.timedelta(7))

    for x in bed_occupancy:
        facility_hfr_code = x.facility_hfr_code
        bed_occupancy_items = core_models.BedOccupancyItems.objects.filter(bed_occupancy_id=bed_occupancy_id).order_by(
            'admission_date')

        if bed_occupancy_items is not None:
            for item in bed_occupancy_items:
                instance_ward = master_data_models.Ward.objects.filter(local_ward_id=item.ward_id,
                                                                       facility__facility_hfr_code=facility_hfr_code).first()

                # Get Patient admission period to add days to it
                instance_patient = core_models.BedOccupancyReport.objects.filter(patient_id=item.patient_id,
                                                                                 admission_date=item.admission_date)

                if instance_patient.count() == 0:
                    get_patient_admission_discharge_period = core_models.BedOccupancyItems.objects.filter(
                        patient_id=item.patient_id, admission_date=item.admission_date,
                        discharge_date=item.discharge_date).first()

                    if get_patient_admission_discharge_period is None:
                        get_patient_admission_period = core_models.BedOccupancyItems.objects.filter(
                            patient_id=item.patient_id,
                            admission_date=item.admission_date).first()

                        if get_patient_admission_period is not None:
                            admission_date = get_patient_admission_period.admission_date
                            discharge_date = bed_occupancy_items.last().admission_date
                        else:
                            get_patient_discharge_period = core_models.BedOccupancyItems.objects.filter(
                                patient_id=item.patient_id,
                                discharge_date=item.discharge_date).first()
                            if get_patient_discharge_period is not None:
                                admission_date = bed_occupancy_items.first().admission_date
                                discharge_date = get_patient_discharge_period.discharge_date
                    else:
                        admission_date = get_patient_admission_discharge_period.admission_date
                        discharge_date = get_patient_admission_discharge_period.discharge_date
                else:
                    pass

                try:
                    bed_occupancy_rate = 1 / int(instance_ward.number_of_beds) * 100

                    create_bed_occupancy_report_record(discharge_date, admission_date, item, bed_occupancy_rate,
                                                       facility_hfr_code)

                except Exception as e:
                    print(e)


def create_bed_occupancy_report_record(discharge_date, admission_date, item, bed_occupancy_rate, facility_hfr_code):
    for x in range(int((discharge_date - admission_date).days)):
        instance_bed_occupancy_report = core_models.BedOccupancyReport()
        instance_bed_occupancy_report.patient_id = item.patient_id
        instance_bed_occupancy_report.date = item.admission_date + datetime.timedelta(days=x)
        instance_bed_occupancy_report.admission_date = item.admission_date
        instance_bed_occupancy_report.ward_id = item.ward_id
        instance_bed_occupancy_report.ward_name = item.ward_name
        instance_bed_occupancy_report.bed_occupancy = bed_occupancy_rate
        instance_bed_occupancy_report.facility_hfr_code = facility_hfr_code
        instance_bed_occupancy_report.save()
