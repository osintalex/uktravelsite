from django.core.management.base import BaseCommand
import json
import logging
import os
import time

import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from keras.models import load_model
from keras.preprocessing.sequence import pad_sequences
import pickle
from corona.models import Country

"""
Run this with python manage.py update-db getdata'.
"""


class Command(BaseCommand):
    data_directory = os.getcwd() + "/corona/data/"

    help = (
        "Run a script to retrieve data from UK Gov API and add to the website database"
    )

    def add_arguments(self, parser):

        # Positional arguments
        parser.add_argument("getdata", nargs="+", type=str)

    def handle(self, *args, **options):

        # Django didn't like it when I tried to import this from another script and call it here
        # So instead have written all these functions here and called them right at the bottom of the script
        # IMO this is messy but I haven't found another way of doing it that would allow me to run a custom command
        # Which is required for this project since I have to schedule running this command

        def get_travel_data(country):
            """
            Makes a get request to the gov API to retrieve travel entry information.
            Corresponding documentation here https://content-api.publishing.service.gov.uk/#quick-start
            :return: None, writes out the output to folder with today's date.
            """

            base_url = "https://www.gov.uk/api/content/foreign-travel-advice/{}/entry-requirements"
            r = requests.get(base_url.format(country), timeout=15)
            if r.status_code == 200:
                parsed = json.loads(r.content)
                with open(Command.data_directory + "{}.txt".format(country), "w") as f:
                    f.write(json.dumps(parsed))
            else:
                logging.info(r.status_code, r.reason)

            return None

        def get_inbound_travel_data():
            """
            Retrieves inbound quarantine information - i.e. current travel corridor list - and writes to file.
            :return: None, writes to json file.
            """

            url = "https://www.gov.uk/api/content/guidance/coronavirus-covid-19-travel-corridors"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                parsed = json.loads(r.content)
                return parsed
            else:
                logging.info(r.status_code, r.reason)

            return None

        def find_coronavirus_and_quarantine_section(country):
            """
            Finds the relevant section about coronavirus in the response.
            :return: Either an empty list if nothing found, a string if only corona restrictions found, a list with
            quarantine and corona information if both found.
            """

            # Load data

            filename = Command.data_directory + "{}.txt".format(country)
            with open(filename, "r") as f:
                response_dict = json.loads(f.read())

            # Define bs4 functions for parsing the data

            def coronavirus_restrictions_h2(tag):
                return tag.name == "h2" and "coronavirus" in tag["id"]

            def coronavirus_restrictions_h3(tag):
                return tag.name == "h3" and "coronavirus" in tag["id"]

            def coronavirus_restrictions_h4(tag):
                return tag.name == "h4" and "coronavirus" in tag["id"]

            def quarantine_requirements_h3(tag):
                return tag.name == "h3" and "quarantine" in tag["id"]

            def quarantine_requirements_h2(tag):
                return tag.name == "h2" and "quarantine" in tag["id"]

            # Get relevant travel information section for the page

            for count, x in enumerate(response_dict["details"]["parts"]):
                if x["title"] == "Entry requirements":
                    target = count

            # Parse the data

            try:
                soup = BeautifulSoup(
                    response_dict["details"]["parts"][target]["body"], "lxml"
                )

                coronavirus_restrictions = soup.find(coronavirus_restrictions_h2)
                if coronavirus_restrictions is None:
                    coronavirus_restrictions = soup.find(coronavirus_restrictions_h3)
                if coronavirus_restrictions is None:
                    coronavirus_restrictions = soup.find(coronavirus_restrictions_h4)
                quarantine_requirements = soup.find(quarantine_requirements_h3)
                if quarantine_requirements is None:
                    quarantine_requirements = soup.find(quarantine_requirements_h2)

                # These countries are all formatted differently so they have a specific section
                if country in ["brazil", "cambodia", "bosnia-and-herzegovina"]:
                    coronavirus_section = []
                    for count, x in enumerate(coronavirus_restrictions.next_elements):
                        if count != 0:
                            coronavirus_section.append(x.previous_element)
                        if x.name == "transiting-{}".format(country):
                            break
                    coronavirus_section = [
                        x.string
                        for x in coronavirus_section
                        if x.string != x.previous_element.string and x.string != None
                    ]
                    coronavirus_section_text = " ".join(coronavirus_section)

                # Now onto all the other countries

                elif country not in ["brazil", "cambodia", "bosnia-and-herzegovina"]:
                    coronavirus_section = []
                    for count, x in enumerate(coronavirus_restrictions.next_elements):
                        if count != 0:
                            coronavirus_section.append(x.previous_element)
                        if (
                            x.name == "h1"
                            or x.name == "h2"
                            or x == quarantine_requirements
                        ):
                            break
                    coronavirus_section = [
                        x.string
                        for x in coronavirus_section
                        if x.string != x.previous_element.string and x.string != None
                    ]
                    coronavirus_section_text = " ".join(coronavirus_section)

                if quarantine_requirements:
                    quarantine_section = []
                    for count, x in enumerate(quarantine_requirements.next_elements):
                        if count != 0:
                            quarantine_section.append(x.previous_element)
                        if x.name == "h2" or x.name == "h1":
                            break
                    quarantine_section = [
                        x.string
                        for x in quarantine_section
                        if x.string != x.previous_element.string and x.string != None
                    ]
                    quarantine_section_text = " ".join(quarantine_section)
                    return coronavirus_section_text, quarantine_section_text

                return coronavirus_section_text

            except Exception as e:
                logging.info(e)
                logging.info(
                    "Failed to identify a relevant section on coronavirus restrictions."
                )

            return []

        def get_travel_data_on_all_countries():
            """
            Gets travel data on all countries and saves  results to file. Must have a countries-list.csv file in root
            directory.
            :return: None, writes output to csv.
            """

            logging.basicConfig(
                filename="Travel Data Logs.txt",
                level=logging.INFO,
                format="%(asctime)s - %(message)s",
            )
            countries_list_filepath = os.getcwd() + "/corona/data/countries-list.csv"
            countries_list = pd.read_csv(
                countries_list_filepath
            )["Countries"].to_list()
            coronavirus_info = []
            quarantine_info = []

            for x in countries_list:
                logging.info("Acquiring data for {}".format(x))
                get_travel_data(x)
                output = find_coronavirus_and_quarantine_section(x)
                if isinstance(output, str):
                    coronavirus_info.append(output)
                    quarantine_info.append("MISSING DATA")
                if isinstance(output, tuple) and output:
                    coronavirus_info.append(output[0])
                    quarantine_info.append(output[1])
                if not output:
                    coronavirus_info.append("MISSING DATA")
                    quarantine_info.append("MISSING DATA")
                time.sleep(0.2)

            df = pd.DataFrame(
                {
                    "Country": countries_list,
                    "Coronavirus Information": coronavirus_info,
                    "Quarantine Information": quarantine_info,
                }
            )
            df.to_csv(Command.data_directory + "outbound-graph-data.csv", index=False)

            return None

        def parse_inbound_data(inbound_data):
            """
            Turns inbound data into csv format.
            :param inbound_data: dictionary of UK Gov API response
            :return: None, writes output to file
            """

            # Turn inbound data into bs4 object and get all the countries on the travel corridor list

            response_dict = inbound_data
            soup = BeautifulSoup(response_dict["details"]["body"], "lxml")
            first_country = soup.find("li")
            country_section = []
            for x in first_country.next_elements:
                if x.name == "h2":
                    break
                country_section.append(x)

            # Tidy up the country list - data comes as very messy

            country_list = set([x.string for x in country_section])
            country_list = [x for x in country_list if x != "\n"]

            # Write out this data to csv

            df = pd.DataFrame({"Country": country_list})
            df["Country"].replace("", np.nan, inplace=True)
            df.dropna(subset=["Country"], inplace=True)
            df.to_csv(Command.data_directory + "inbound-graph-data.csv", index=False)

            return None

        def assign_scores():
            """
            Assign numerical scores in the form of floats to the outbound dataframe.
            Uses a ML model built with keras.
            :return: None, writes to file
            """

            # Import data, model, tokenzier

            corona_model = load_model(
                Command.data_directory + "Corona Travel Info model"
            )

            # Write out sentiment analysis predictions for corona info

            df = pd.read_csv(Command.data_directory + "outbound-graph-data.csv")
            df = df[~df["Coronavirus Information"].str.contains("MISSING DATA")]

            with open(
                Command.data_directory + "coronavirus-tokenizer.pickle", "rb"
            ) as handle:
                coronavirus_tokenizer = pickle.load(handle)

            predictions = []
            for x in df["Coronavirus Information"]:
                x = coronavirus_tokenizer.texts_to_sequences([x])
                x = pad_sequences(x, maxlen=200)
                prediction = corona_model.predict(x)
                predictions.append(prediction[0][0])

            # Write out dataframe to csv

            df["Travel Sentiment Score"] = predictions
            df.to_csv(Command.data_directory + "outbound-graph-data.csv")

            return

        def add_dates():
            """
            Add the date this information was created.
            Allows the website to make SQL query statements only on today's date to ensure all the travel info is
            current.
            :return: None
            """

            outbound = pd.read_csv(Command.data_directory + "outbound-graph-data.csv")
            inbound = pd.read_csv(Command.data_directory + "inbound-graph-data.csv")

            outbound["Date"] = pd.Timestamp("today").strftime("%Y-%m-%d")
            inbound["Date"] = pd.Timestamp("today").strftime("%Y-%m-%d")

            outbound.to_csv(
                Command.data_directory + "outbound-graph-data.csv", index=False
            )
            inbound.to_csv(
                Command.data_directory + "inbound-graph-data.csv", index=False
            )

            return None

        # Call all the above functions to retrieve data from the UK Gov API, classify text sentiment

        get_travel_data_on_all_countries()
        parse_inbound_data(get_inbound_travel_data())
        assign_scores()
        add_dates()

        # Populate the Django database with the above data

        outbound_filepath = Command.data_directory + "outbound-graph-data.csv"
        outbound = pd.read_csv(outbound_filepath)
        outbound_as_dict = outbound.to_dict("records")

        model_instances = [
            Country(
                name=x["Country"],
                corona=x["Coronavirus Information"],
                quarantine=x["Quarantine Information"],
                date_of_information=x["Date"],
                sentiment=x["Travel Sentiment Score"],
            )
            for x in outbound_as_dict
        ]

        Country.objects.bulk_create(model_instances)
