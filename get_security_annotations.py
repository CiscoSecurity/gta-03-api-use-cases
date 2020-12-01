#!/usr/bin/python

from __future__ import print_function
import requests
import os
import sys
import datetime
import json

CUSTOMER_ID = "YOUR_CUSTOMER_ID"
ACCESS_TOKEN = "YOUR_VALID_ACCESS_TOKEN"

PREVIOUS_SIGHTING_MODIFIED_AT_FILENAME = "previous_sighting_modified_at.txt"

API_HOST_NAME = "https://api.cta.eu.amp.cisco.com"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def parse_iso_datetime(iso_datetime):
    try:
        return datetime.datetime.strptime(iso_datetime, DATETIME_FORMAT)
    except ValueError:
        sys.stderr.write("Error: failed to parse datetime: \"" + iso_datetime + "\"\n")


def read_max_sighting_modified_at():
    if os.path.isfile(PREVIOUS_SIGHTING_MODIFIED_AT_FILENAME):
        try:
            previous_sighting_modified_at_file = open(PREVIOUS_SIGHTING_MODIFIED_AT_FILENAME, "r")
            previous_sighting_modified_at = parse_iso_datetime(previous_sighting_modified_at_file.readline())
            previous_sighting_modified_at_file.close()
            return previous_sighting_modified_at
        except IOError:
            sys.stderr.write("Error: failed to read max sighting modifiedAt: " + PREVIOUS_SIGHTING_MODIFIED_AT_FILENAME + "\n")
            sys.exit(1)
    else:
        return datetime.datetime.fromtimestamp(0)


def write_max_sighting_modified_at(max_sighting_modified_at):
    try:
        previous_sighting_modified_at_file = open(PREVIOUS_SIGHTING_MODIFIED_AT_FILENAME, "w")
        previous_sighting_modified_at_file.write(max_sighting_modified_at.strftime(DATETIME_FORMAT))
        previous_sighting_modified_at_file.close()

    except IOError:
        sys.stderr.write("Error writing max sighting modifiedAt: " + PREVIOUS_SIGHTING_MODIFIED_AT_FILENAME + "\n")
        sys.exit(2)


class CollectionIterator:

    def __init__(self, collection_url):
        self.has_api_response = False
        self.has_next_page = None
        self.next_page_url = collection_url
        self.current_page_items = []
        self.current_page_items_pointer = 0

    def has_next(self):
        if not self.has_api_response:
            self.__fetch_next_page()

        return self.__has_current_page_items() or self.has_next_page

    def next(self):
        if not self.has_api_response \
                or (not self.__has_current_page_items() and self.has_next_page):
            self.__fetch_next_page()

        if self.__has_current_page_items():
            item = self.current_page_items[self.current_page_items_pointer]
            self.current_page_items_pointer = self.current_page_items_pointer + 1
            return item
        else:
            return None

    def __fetch_next_page(self):
        print(API_HOST_NAME + self.next_page_url)
        response = requests.get(API_HOST_NAME + self.next_page_url,
                                headers={
                                    "Authorization": "Bearer " + ACCESS_TOKEN,
                                    "Accept": "application/json"
                                })
        print(response.text)
        data = response.json()
        self.has_next_page = data["pageInfo"]["hasNextPage"]
        self.next_page_url = data["pageInfo"]["next"]
        self.current_page_items = data["items"]
        self.current_page_items_pointer = 0
        self.has_api_response = True

    def __has_current_page_items(self):
        return self.current_page_items_pointer < len(self.current_page_items)


def build_alert_threat_occurrences_url(alert_id):
    return "/alert-management/customer/" + CUSTOMER_ID + "/alerts/" + alert_id + "/threat-occurrences"


def build_threat_occurrence_convicting_sightings_url(threat_occurrence_id):
    return "/threat-detection/customer/" + CUSTOMER_ID + "/threat-occurrences/" + threat_occurrence_id + "/sightings/convicting"


def build_threat_occurrence_contextual_sightings_url(threat_occurrence_id):
    return "/threat-detection/customer/" + CUSTOMER_ID + "/threat-occurrences/" + threat_occurrence_id + "/sightings/contextual"


def log_sighting_attributes(alert, threat_occurrence, sighting):
    row = {
        "indexTime": datetime.datetime.now().strftime(DATETIME_FORMAT),
        "alertId": alert["id"],
        "alertState": alert["state"],
        "risk": alert["risk"],
        "affectedAssetId": threat_occurrence["affectedAssetId"],
        "threatOccurrenceId": threat_occurrence["id"],
        "confidence": threat_occurrence["confidence"],
        "sightingId": sighting["id"],
        "sightingDetectedAt": sighting["detectedAt"],
        "sightingModifiedAt": sighting["modifiedAt"],
        "severity": sighting["severity"],
        "eventTypeId": sighting["eventTypeId"],
        "sightingTitle": sighting["title"],
        "sightingSubtitle": sighting["subtitle"],
    }

    if sighting["securityAnnotation"]:
        row.update({
            "securityAnnotationId": sighting["securityAnnotation"]["id"],
            "securityAnnotationAttributes": sighting["securityAnnotation"]["requiredAttributes"]
        })

    print(json.dumps(row))


def process_sightings(alert, threat_occurrence, sightings_iterator, previous_max_sighting_modified_at, max_sighting_modified_at):
    while sightings_iterator.has_next():
        sighting = sightings_iterator.next()

        modified_at_sighting_datetime = parse_iso_datetime(sighting["modifiedAt"])
        if modified_at_sighting_datetime > previous_max_sighting_modified_at:
            log_sighting_attributes(alert, threat_occurrence, sighting)

            if modified_at_sighting_datetime > max_sighting_modified_at:
                max_sighting_modified_at = modified_at_sighting_datetime

    return max_sighting_modified_at


def main():
    # get maximal "modifiedAt" from all processed Sightings stored after previous run
    previous_max_sighting_modified_at = read_max_sighting_modified_at()
    # variable holding "modifiedAt" maximum for all Sightings currently processed
    max_sighting_modified_at = previous_max_sighting_modified_at

    alerts_iterator = CollectionIterator("/alert-management/customer/" + CUSTOMER_ID + "/alerts")

    # iterate through all alerts
    while alerts_iterator.has_next():
        alert = alerts_iterator.next()

        threat_occurrences_iterator = CollectionIterator(build_alert_threat_occurrences_url(alert["id"]))

        # iterate through all threat_occurrences
        while threat_occurrences_iterator.has_next():
            threat_occurrence = threat_occurrences_iterator.next()

            # iterate through all convicting sightings
            convicting_sightings_iterator = CollectionIterator(build_threat_occurrence_convicting_sightings_url(threat_occurrence["id"]))
            max_sighting_modified_at = process_sightings(alert, threat_occurrence, convicting_sightings_iterator, previous_max_sighting_modified_at, max_sighting_modified_at)

            # iterate through all contextual sightings
            contextual_sightings_iterator = CollectionIterator(build_threat_occurrence_contextual_sightings_url(threat_occurrence["id"]))
            max_sighting_modified_at = process_sightings(alert, threat_occurrence, contextual_sightings_iterator, previous_max_sighting_modified_at, max_sighting_modified_at)

    # persist maximal "modifiedAt" for next run
    write_max_sighting_modified_at(max_sighting_modified_at)


main()
