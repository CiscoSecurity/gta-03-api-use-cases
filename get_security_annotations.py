#!/usr/bin/python

from __future__ import print_function
import os
import sys
import datetime
import json
from api_client import ApiClient

SECUREX_CLIENT_ID = "YOUR_SECUREX_CLIENT_ID"
SECUREX_CLIENT_PASSWORD = "YOUR_SECUREX_CLIENT_PASSWORD"
SECUREX_VISIBILITY_HOST_NAME = "YOUR_SECUREX_VISIBILITY_HOST_NAME"

# Filename (including full path) to save cursor of then last processed event item.
# It creates a new file, if the file does not exist otherwise truncates and over-write existing file.
# Needs read/write access to the folder, e.g. "/home/splunk/events_end_cursor.txt"
EVENTS_END_CURSOR_FILENAME = "/events_end_cursor.txt"

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def read_events_end_cursor():
    if os.path.isfile(EVENTS_END_CURSOR_FILENAME):
        try:
            with open(EVENTS_END_CURSOR_FILENAME, "r") as events_end_cursor_file:
                events_end_cursor = events_end_cursor_file.readline()
                return events_end_cursor
        except IOError:
            sys.stderr.write("Error: failed to read events end cursor: " + EVENTS_END_CURSOR_FILENAME + "\n")
            sys.exit(1)


def write_events_end_cursor(events_end_cursor):
    try:
        with open(EVENTS_END_CURSOR_FILENAME, "w") as events_end_cursor_file:
            events_end_cursor_file.write(events_end_cursor)
    except IOError:
        sys.stderr.write("Error writing events end cursor: " + EVENTS_END_CURSOR_FILENAME + "\n")
        sys.exit(2)


def build_alerts_search_url(customer_id):
    return "/alert-management/customer/" + customer_id + "/alerts/search"


def build_assets_search_url(customer_id):
    return "/asset-management/customer/" + customer_id + "/assets/search"


def build_threat_intel_url():
    return "/threat-catalog/records"


def build_search_threat_detection_with_alert_id_url(customer_id):
    return "/alert-management/customer/" \
           + customer_id \
           + "/enriched-threat-detections-with-alert-ids/search"


def build_event_with_threat_detections_ids_url(customer_id):
    return "/threat-detection/customer/" \
           + customer_id \
           + "/enriched-events-with-threat-detection-ids"


def log_event_attributes(event, affected_asset=None, threat_detection=None, threat_intel_record=None, alert=None):
    row = {
        "indexTime": datetime.datetime.now().strftime(DATETIME_FORMAT),
        "eventId": event["id"],
        "eventDetectedAt": event["detectedAt"],
        "eventModifiedAt": event["modifiedAt"],
        "securityEventTypeId": event["securityEventTypeId"],
        "eventTitle": event["title"],
        "eventSubtitle": event["subtitle"],
    }

    if affected_asset:
        row.update({
            "assumedOwner": affected_asset["assumedOwner"],
        })

    if alert:
        row.update({
            "alertId": alert["id"],
            "alertState": alert["state"],
            "risk": alert["risk"],
        })

    if threat_intel_record:
        row.update({
            "threatTitle": threat_intel_record["title"],
            "threatCategory": threat_intel_record["category"],
            "threatSubCategory": threat_intel_record["subcategory"],
            "severity": threat_intel_record["severity"],
        })

    if threat_detection:
        row.update({
            "affectedAssetId": threat_detection["affectedAssetId"],
            "threatDetectionId": threat_detection["id"],
            "confidence": threat_detection["confidence"],
        })

    if event["securityAnnotation"]:
        row.update({
            "securityAnnotationId": event["securityAnnotation"]["id"],
            "securityAnnotationAttributes": event["securityAnnotation"]["requiredAttributes"]
        })

    print(json.dumps(row))


def main():
    api_client = ApiClient(SECUREX_VISIBILITY_HOST_NAME, SECUREX_CLIENT_ID, SECUREX_CLIENT_PASSWORD)

    # read stored cursor of last security event item from previous script run (if any)
    # to process only new or modified events in current script run
    previous_events_end_cursor = read_events_end_cursor()

    # USE BULK LOADING RESOURCES ON API TO PRELOAD EVENTS AND IMPORTANT REFERRED OBJECTS

    # remember events
    events = []
    # cached contextual objects - alerts, threat detections, threat intel records, assets
    cached_context_objects = {}

    threat_detection_ids = []
    affected_asset_ids = []

    # iterate over all security events sorted by unique modification sequence number ensuring no event is missed
    events_iterator = api_client.create_collection_iterator(
        collection_url_path=build_event_with_threat_detections_ids_url(api_client.get_customer_id()),
        query_params={
            "sort": "modificationSequenceNumber",
        },
        cursor=previous_events_end_cursor
    )
    # remember events and get ids of related object (threat detections and assets) to "bulk load" them
    for event in events_iterator:
        events.append(event)
        threat_detection_ids.extend(event["threatDetectionIds"])
        affected_asset_ids.append(event["affectedAssetId"])

    # bulk load threat detections by their ids
    threat_detections_iterator = api_client.create_collection_iterator(
        collection_url_path=build_search_threat_detection_with_alert_id_url(api_client.get_customer_id()),
        request_body={
            "filter": {
                "threatDetectionIds": list(set(threat_detection_ids))
            }
        }
    )

    alert_ids = []
    threat_intel_record_ids = []

    # keep threat detections in "cached_context_objects" and extract IDs of alerts and threat intel records
    for threat_detection in threat_detections_iterator:
        cached_context_objects[threat_detection["id"]] = threat_detection
        alert_ids.extend(threat_detection["alertIds"])
        threat_intel_record_ids.append(threat_detection["threatIntelRecordId"])

    # bulk load assets by their ids
    affected_asset_iterator = api_client.create_collection_iterator(
        collection_url_path=build_assets_search_url(api_client.get_customer_id()),
        request_body={
            "filter": {
                "assetId": list(set(affected_asset_ids))
            }
        }
    )

    # keep assets in "cached_context_objects"
    for affected_asset in affected_asset_iterator:
        cached_context_objects[affected_asset["id"]] = affected_asset

    # bulk load alerts
    alerts_iterator = api_client.create_collection_iterator(
        collection_url_path=build_alerts_search_url(api_client.get_customer_id()),
        request_body={
            "filter": {
                "alertIds": list(set(alert_ids))
            }
        }
    )

    # keep alerts in "cached_context_objects"
    for alert in alerts_iterator:
        cached_context_objects[alert["id"]] = alert

    # bulk load threat intelligence records
    threat_intel_records_iterator = api_client.create_collection_iterator(
        collection_url_path=build_threat_intel_url(),
        request_body={
            "filter": {
                "threatIntelRecordId": list(set(threat_intel_record_ids))
            }
        }
    )

    # keep threat intelligence records in "cached_context_objects"
    for threat_intel_record in threat_intel_records_iterator:
        cached_context_objects[threat_intel_record["id"]] = threat_intel_record

    # PROCESS EVENTS AND OTHER CONTEXTUAL OBJECTS

    # start with events, get contextual objects for each event from cached_context_objects and log them together
    for event in events:
        # get affected asset referred by event
        affected_asset = cached_context_objects.get(event["affectedAssetId"], None)

        # get IDs references to threat detections from event (usually one, can be [])
        threat_detection_ids = event["threatDetectionIds"]

        # process event with threat detections (called "convicting" security event)
        for threat_detection_id in threat_detection_ids:
            # get parent objects to event - threat detections and alert
            # and also threat intel record from threat-catalog bounded context
            threat_detection_with_alert_ids = cached_context_objects.get(threat_detection_id, None)
            threat_intel_record = cached_context_objects.get(threat_detection_with_alert_ids["threatIntelRecordId"], None) if threat_detection_with_alert_ids else None

            # get IDs references to alerts (usually one)
            alert_ids = threat_detection_with_alert_ids["alertIds"] if threat_detection_with_alert_ids else []
            for alert_id in alert_ids:
                alert = cached_context_objects.get(alert_id, None)

                # log event with all related objects - alert, threat detection, threat intel record
                log_event_attributes(event, affected_asset, threat_detection_with_alert_ids, threat_intel_record, alert)
            else:
                # process event with missing threat detection or missing alert (might be GC)
                log_event_attributes(event, affected_asset, threat_detection_with_alert_ids, threat_intel_record)
        else:
            # process event without threat detections (called "contextual" security event)
            # log event just with affected_asset
            log_event_attributes(event, affected_asset)

    # store events end_cursor for next script run
    if events_iterator.end_cursor():
        write_events_end_cursor(events_iterator.end_cursor())


if __name__ == "__main__":
    main()
