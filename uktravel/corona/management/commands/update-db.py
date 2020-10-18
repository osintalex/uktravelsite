import pandas as pd
import os
from django.core.management.base import BaseCommand, CommandError
from corona.models import Country

"""
Run this with python manage.py update-db getdata
"""

class Command(BaseCommand):
    help = 'Run a script to retrieve data from UK Gov API and add to the website database'

    def add_arguments(self, parser):
        parser.add_argument('getdata', nargs='+', type=str)

    def handle(self, *args, **options):

        filepath = os.getcwd() + "/corona/Coronavirus Travel Data for All Countries.csv"
        df = pd.read_csv(filepath)
        df_as_dict = df.to_dict('records')

        model_instances = [Country(
            name=x['Country'],
            corona=x['Coronavirus Information'],
            quarantine=x['Quarantine Information'],
            date_of_information=x['Date'],
        ) for x in df_as_dict]

        Country.objects.bulk_create(model_instances)