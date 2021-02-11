#!/usr/bin/python

from __future__ import print_function
import requests
import os
import sys
import datetime
import json

CUSTOMER_ID = "YOUR_CUSTOMER_ID"
ACCESS_TOKEN = "YOUR_VALID_ACCESS_TOKEN"

PREVIOUS_EVENT_MODIFIED_AT_FILENAME = "previous_event_modified_at.txt"

API_HOST_NAME = "https://api.cta.eu.amp.cisco.com"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def parse_iso_datetime(iso_datetime):
    try:
        return datetime.datetime.strptime(iso_datetime, DATETIME_FORMAT)
    except ValueError:
        sys.stderr.write("Error: failed to parse datetime: \"" + iso_datetime + "\"\n")


def read_max_event_modified_at():
    if os.path.isfile(PREVIOUS_EVENT_MODIFIED_AT_FILENAME):
        try:
            previous_event_modified_at_file = open(PREVIOUS_EVENT_MODIFIED_AT_FILENAME, "r")
            previous_event_modified_at = parse_iso_datetime(previous_event_modified_at_file.readline())
            previous_event_modified_at_file.close()
            return previous_event_modified_at
        except IOError:
            sys.stderr.write("Error: failed to read max event modifiedAt: " + PREVIOUS_EVENT_MODIFIED_AT_FILENAME + "\n")
            sys.exit(1)
    else:
        return datetime.datetime.fromtimestamp(0)


def write_max_event_modified_at(max_event_modified_at):
    try:
        previous_event_modified_at_file = open(PREVIOUS_EVENT_MODIFIED_AT_FILENAME, "w")
        previous_event_modified_at_file.write(max_event_modified_at.strftime(DATETIME_FORMAT))
        previous_event_modified_at_file.close()

    except IOError:
        sys.stderr.write("Error writing max event modifiedAt: " + PREVIOUS_EVENT_MODIFIED_AT_FILENAME + "\n")
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
        response = requests.get(API_HOST_NAME + self.next_page_url,
                                headers={
                                    "Authorization": "Bearer " + ACCESS_TOKEN,
                                    "Accept": "application/json"
                                })
        data = response.json()
        self.has_next_page = data["pageInfo"]["hasNextPage"]
        self.next_page_url = data["pageInfo"]["next"]
        self.current_page_items = data["items"]
        self.current_page_items_pointer = 0
        self.has_api_response = True

    def __has_current_page_items(self):
        return self.current_page_items_pointer < len(self.current_page_items)


def build_alert_threat_detections_url(alert_id):
    return "/alert-management/customer/" + CUSTOMER_ID + "/alerts/" + alert_id + "/threat-detections"


def build_threat_detection_convicting_events_url(threat_detection_id):
    return "/threat-detection/customer/" + CUSTOMER_ID + "/threat-detections/" + threat_detection_id + "/events/convicting"


def build_threat_detection_contextual_events_url(threat_detection_id):
    return "/threat-detection/customer/" + CUSTOMER_ID + "/threat-detections/" + threat_detection_id + "/events/contextual"


def log_event_attributes(alert, threat_detection, event):
    row = {
        "indexTime": datetime.datetime.now().strftime(DATETIME_FORMAT),
        "alertId": alert["id"],
        "alertState": alert["state"],
        "risk": alert["risk"],
        "affectedAssetId": threat_detection["affectedAssetId"],
        "threatDetectionId": threat_detection["id"],
        "confidence": threat_detection["confidence"],
        "eventId": event["id"],
        "eventDetectedAt": event["detectedAt"],
        "eventModifiedAt": event["modifiedAt"],
        "severity": event["severity"],
        "eventTypeId": event["eventTypeId"],
        "eventTitle": event["title"],
        "eventSubtitle": event["subtitle"],
    }

    if event["securityAnnotation"]:
        row.update({
            "securityAnnotationId": event["securityAnnotation"]["id"],
            "securityAnnotationAttributes": event["securityAnnotation"]["requiredAttributes"]
        })

    print(json.dumps(row))


def process_events(alert, threat_detection, events_iterator, previous_max_event_modified_at, max_event_modified_at):
    while events_iterator.has_next():
        event = events_iterator.next()

        modified_at_event_datetime = parse_iso_datetime(event["modifiedAt"])
        if modified_at_event_datetime > previous_max_event_modified_at:
            log_event_attributes(alert, threat_detection, event)

            if modified_at_event_datetime > max_event_modified_at:
                max_event_modified_at = modified_at_event_datetime

    return max_event_modified_at


def main():
    # get maximal "modifiedAt" from all processed Sightings stored after previous run
    previous_max_event_modified_at = read_max_event_modified_at()
    # variable holding "modifiedAt" maximum for all Sightings currently processed
    max_event_modified_at = previous_max_event_modified_at

    alerts_iterator = CollectionIterator("/alert-management/customer/" + CUSTOMER_ID + "/alerts")

    # iterate through all alerts
    while alerts_iterator.has_next():
        alert = alerts_iterator.next()

        threat_detections_iterator = CollectionIterator(build_alert_threat_detections_url(alert["id"]))

        # iterate through all threat_detections
        while threat_detections_iterator.has_next():
            threat_detection = threat_detections_iterator.next()

            # iterate through all convicting events
            convicting_events_iterator = CollectionIterator(build_threat_detection_convicting_events_url(threat_detection["id"]))
            max_event_modified_at = process_events(alert, threat_detection, convicting_events_iterator, previous_max_event_modified_at, max_event_modified_at)

            # iterate through all contextual events
            contextual_events_iterator = CollectionIterator(build_threat_detection_contextual_events_url(threat_detection["id"]))
            max_event_modified_at = process_events(alert, threat_detection, contextual_events_iterator, previous_max_event_modified_at, max_event_modified_at)

    # persist maximal "modifiedAt" for next run
    write_max_event_modified_at(max_event_modified_at)


main()
