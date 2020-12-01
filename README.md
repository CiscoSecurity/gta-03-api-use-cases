# Using Cognitive Intelligence API

You'll need a valid `ACCESS_TOKEN` to access Cognitive Intelligence API.

Most resources require you to know your `CUSTOMER_ID`. You can find it in [Cognitive Intelligence UI](https://cognitive.cisco.com/ui) under the user icon in the main navigation.

## Basic usage

Use the `/alerts` resource to get `Alerts`:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts
```

You'll get a paginated collection response:

```jsonc
{
  "items": [
    {
      "id": "1404846aee08468007331ad8374ce2d796697dacc70a8f7e0e82d02cfd355057",
      "risk": "Critical",
      "state": "Remediated",
      "etaFlag": "EtaBasedDetection",
      "note": "string",
      "triggeredAt": "2020-10-14T13:59:54.047Z",
      "modifiedAt": "2020-10-14T13:59:54.047Z"
    }
  ],
  "pageInfo": { /* object */ },
}
```

You can learn more about [how the pagination works](#pagination) or see our example on [how to use pagination to get all collection items](#getting-all-items).

## Synchronize Alerts

### Get new Alerts triggered since the last synchronization

For initial synchronization of `Alerts`, use the `/alerts` resource with `sort=triggeredAt:asc` parameter, eg:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts?sort=triggeredAt:asc
```

To get only newly created alerts in subsequent synchronizations:

1. take `triggeredAt` of last alert from previous request (it's the latest because of `sort=triggeredAt:asc`)
1. use it for new request as a `triggeredSince` parameter

Eg:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts?triggeredSince=2020-09-05T12:00:00Z&sort=triggeredAt:asc
```

See [Date-time format](#date-time-format) for more information about `triggeredSince` format.

### Get modified (and new) Alerts since a specific point in time

Use the `/alerts` resource with `modifiedSince=[date-time]` parameter, eg:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts?modifiedSince=2020-09-05T12:00:00Z
```
You'll get all alerts with `Alert.modifiedAt` value greater than value requested in `modifiedSince` parameter.

See [Date-time format](#date-time-format) for more information about `modifiedSince` format.

`Alert.modifiedAt` is initially the same as `Alert.triggeredAt` but changes when:

* The `Alert` content changes (eg. `risk`, `state`, `etaFlag`, `note`).
* `ThreatOccurrence` is added to the `Alert`.
* `ThreatOccurrence` is removed from the `Alert`.

### Synchronize previously saved Alerts one by one

To synchronize `Alerts` you already requested before you have these options:

* Repeat the original request to get all the alerts.
* Query saved alerts one by one. If alert was removed you'll get `404 Not Found` as a response.

> `Alert` is removed when all its related `ThreatOccurrence`s time out.
> `ThreatOccurrence` times out after 45 days since its latest detected malicious activity.

## Get a single Alert

To get one Alert with a known `id`, use:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts/${ALERT_ID}
```

## Update Alert state

To change Alert state, use:

```console
$ curl -X PATCH \
       -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
       -H "Content-Type: application/json" \
       --data '{"state":"Remediated"}' \
  https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts/${ALERT_ID}/state
```

Available `AlertState` values:

* `New`
* `Investigating`
* `Remediating`
* `Remediated`
* `Ignored`
* `FalsePositive`

> To reset Alert state back to `New`, you can also call `DELETE` method on the `/state` resource.

## Update Alert note

To change Alert note, use:

```console
$ curl -X PATCH \
       -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
       -H "Content-Type: application/json" \
       --data '{"note":"Started investigation, our internal ticket ID=XXXXXX"}' \
  https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts/${ALERT_ID}/note
```

_**Caution:** When the alert is in the New state, the note may get deleted when alerts are recalculated. To prevent this, change the state of the alert to not New._

> To remove note call `DELETE` method on `/note` resource.

## Date-time format

For parameters like `triggeredSince`, `modifiedSince`, etc. use ISO 8601 date-time format as defined by [RFC 3339, section 5.6](https://tools.ietf.org/html/rfc3339#section-5.6).

Same format is also used for all date-time information in API responses.

> On Unix system you can use `date -u -v-45d +"%Y-%m-%dT%H:%M:%SZ"` to get the date of 45 days in the past in the correct format.

## Pagination

All resources providing a collection of items are paginated by default. Cursor based pagination is used.

### Paginated response

All paginated resource responses adhere to the following shape:

```jsonc
{
  "items": [ /* array */ ],
  "pageInfo": { /* object */ }
}
```

#### Items

`items` array contains found objects.

In case there are no matching objects available, `items` is an empty array `[]`.

Example:

```jsonc
{
  "items": [
    {
      "id": "1404846aee08468007331ad8374ce2d796697dacc70a8f7e0e82d02cfd355057",
      "risk": "Critical",
      "state": "Remediated",
      "etaFlag": "EtaBasedDetection",
      "note": "string",
      "triggeredAt": "2020-10-14T13:59:54.047Z",
      "modifiedAt": "2020-10-14T13:59:54.047Z"
    }
   ],
  "pageInfo": { /* object */ }
}
```

#### Page Info

`pageInfo` contains details about the current page and ways how to get the next and previous page. It's the same for all collection responses.

Example:

```jsonc
    {
      "items": [ /* array */ ],
      "pageInfo": {
        "previous": "/alert-management/customer/CTA123456789/alerts?size=10&before=b641415c-fa6a-467d-b052-5a3deacf2992",
        "next": "/alert-management/customer/CTA123456789/alerts?size=10&after=32c43ccb-20b7-4e39-a2ab-d05791ae23f0",
        "hasNextPage": true,
        "hasPreviousPage": false,
        "startCursor": "High,b641415c-fa6a-467d-b052-5a3deacf2992",
        "endCursor": "High,32c43ccb-20b7-4e39-a2ab-d05791ae23f0"
      }
    }
```

Fields:

* `previous`
  * relative path to the previous page
  * if the previous page does not exist, `null` is returned
* `next`
  * relative path to the next page
  * if the next page does not exist, `null` is returned.
* `hasPreviousPage` 
  * boolean value about the previous page existence
  * `true` means the previous page is available
* `hasNextPage`
  * boolean value about the next page existence
  * `true` means the next page is available
* `startCursor`
  * value identifies the first item in the current results
  * should be used to construct a request for the previous page
  * when the previous page is not available, `null` is returned
* `endCursor`
  * value identifies the last item in the current results
  * should be used to construct a request for the next page
  * when the next page is not available, `null` is returned

### Limiting results

To limit how many items should be returned, use `size=[number]` query string parameter.

Maximum number of requested items is `1,000`.

> This limit is also applied when requesting collection without the `size` parameter.

Example:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts?size=10
```

### Getting the next page

To get the next page of previous response, use `after=[endCursor]` query parameter in your next request, eg:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  https://api.cta.eu.amp.cisco.com/alert-management/customer/CTA123456789/alerts?size=10&after=32c43ccb-20b7-4e39-a2ab-d05791ae23f0
```

> You can also use the `next` link from the `pageInfo`.

> The similar situation is when you'd like to get `previous` page. You just need to use `before=[startCursor]` as parameter.

### Getting all items

To get all collection items, call `next` page URLs from the previous responses until next page is not available (`hasNextPage=false`).

Written in simplified code for alerts it can be logically done like in this python snippet:

```python
import requests

CUSTOMER_ID = "YOUR_CUSTOMER_ID"
ACCESS_TOKEN = "YOUR_VALID_ACCESS_TOKEN"

API_HOST_NAME = "https://api.cta.eu.amp.cisco.com"
FETCH_ALERTS_URL = "/alert-management/customer/" + CUSTOMER_ID + "/alerts"


def get_all_alerts():
    alerts = []
    fetch_url = FETCH_ALERTS_URL

    while True:
        # request for page of item
        response = requests.get(API_HOST_NAME + fetch_url,
                                headers={
                                    "Authorization": "Bearer " + ACCESS_TOKEN,
                                    "Accept": "application/json"
                                })
        data = response.json()

        # collect all received items together, preserve order
        alerts = alerts + data["items"]

        # set fetchUrl to next page
        fetch_url = data["pageInfo"]["next"]

        # repeat loop when next page is available
        if not data["pageInfo"]["hasNextPage"]:
            break

    return alerts


print(get_all_alerts())
```

> This script is available in the `get_all_alerts.py` file.

## Synchronizing external SIEM

In addition to `Alerts`, Cognitive Intelligence API also offers more granular information like `ThreatOccurrences` or `Sightings`.

> Learn more about `ThreatOccurrence` and `Sighting` in
>[Cognitive Intelligence Documentation](http://www.cisco.com/c/en/us/td/docs/security/web_security/scancenter/administrator/guide/b_ScanCenter_Administrator_Guide/b_ScanCenter_Administrator_Guide_chapter_011110.html)
>.

To get the first page of `ThreatOccurrences`, use the following query:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  https://api.cta.eu.amp.cisco.com/threat-detection/customer/{CUSTOMER_ID}/threat-occurrences
```

To get the first page of `Sightings`:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  https://api.cta.eu.amp.cisco.com/network-behavior-anomaly-detection/customer/{CUSTOMER_ID}/sightings
```

Each convicting `Sighting` can belong to one or more `ThreatOccurrences`. This can lead to processing a single convicting `Sighting` multiple times. However relation to multiple `ThreatOccurrences` is quite rare.

Most convicting `Sightings` contain `securityAnnotation`, which represents key observations used for detecting threat or malicious behavior.

### Iterating over Sightings hierarchically with an Alert and a ThreatOccurrence in the context

To put everything together:

1. Iterate over all `Alerts` (as described in previous sections).
1. For each `Alert`, iterate over all its `ThreatOccurrences`.
1. For each `ThreatOccurrence`, iterate over all its convicting `Sightings`.

Optionally, to get a better insight, you can also iterate over all contextual `Sightings` using:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  https://api.cta.eu.amp.cisco.com/threat-detection/customer/{CUSTOMER_ID}/threat-occurrences/{THERAT_OCCURRENCE_ID}/sightings/contextual
```

Beware that each contextual `Sighting` spotted on particular `Asset` belongs to every
`ThreatOccurrence` detected on this `Asset`. Therefore it's quite common for one contextual `Sighting` to belong to several
`ThreatOccurrences`. This can lead to processing a single contextual `Sighting` multiple times.

#### Example

```python
CUSTOMER_ID = "YOUR_CUSTOMER_ID"


def build_alert_threat_occurrences_url(alert_id):
    return "/alert-management/customer/" + CUSTOMER_ID + "/alerts/" + alert_id + "/threat-occurrences"


def build_threat_occurrence_convicting_sightings_url(threat_occurrence_id):
    return "/threat-detection/customer/" + CUSTOMER_ID + "/threat-occurrences/" + threat_occurrence_id + "/sightings/convicting"


def start():
    alerts_iterator = CollectionIterator("/alert-management/customer/" + CUSTOMER_ID + "/alerts")

    while alerts_iterator.has_next():
        alert = alerts_iterator.next()

        threat_occurrences_iterator = CollectionIterator(build_alert_threat_occurrences_url(alert["id"]))

        while threat_occurrences_iterator.has_next():
            threat_occurrence = threat_occurrences_iterator.next()

            sightings_iterator = CollectionIterator(build_threat_occurrence_convicting_sightings_url(threat_occurrence["id"]))

            while sightings_iterator.has_next():
                sighting = sightings_iterator.next()
                process_sighting(alert, threat_occurrence, sighting)
```

> `CollectionIterator` class is available in the `get_security_annotations.py` file. It implements `has_next` and `next` methods to be able to go through all pages of items of each individual collection.

Method `process_sighting` represents whatever processing of  `Sighting` you wish to do, with access to the parent `ThreatOccurrence` and its parent `Alert`.

For simplicity we ignore potential duplicities of convicting `Sightings`.

#### Repeated iterations over Sightings

To automate the process of working with `Sightings`, e.g. for importing to SIEM, you usually need to process
only new or updated `Sightings`.

Each `Sighting` (and `ThreatOccurrence`) has two date fields available:

* `detectedAt` - instant when this entity was created by the classification engine
* `modifiedAt` - instant when this entity was last updated by the classification engine

Each `Sighting` and `ThreatOccurrence` can change over time, so use use `modifiedAt` when interested in all the updates.

When running first synchronization of `Sightings`, saving `modifiedAt` is important for the next synchronization, especially maximum `modifiedAt` value across all `Sightings`.

In all subsequent synchronizations, compare each `Sighting.modifiedAt` with maximum `modifiedAt` from previous
synchronization to process only new or updated `Sightings`.

> Because `Sighting` observables are aggregated, it's not possible to distinguish between old attributes values and new ones. `Sighting` needs to be processed as a whole.

### Importing Sightings to Splunk

Working example script is available in the  `get_security_annotations.py` file. It can be used as a template for writing more complex scripts.

> Python 2.7+ is required to run the code.

To get started, modify the example script and provide your:

* `CUSTOMER_ID`
* valid `ACCESS_TOKEN`
* full path to the file in `PREVIOUS_SIGHTING_MODIFIED_AT_FILENAME`

The script output is generated in `log_sighting_attributes` method and it's in JSON format. Use Splunk's pre-defined
source type `_json` to process output of the script.

After each run, the example script persists maximal `modifiedAt` across all processed `Sightings`.

To run full
processing again, delete the file specified in the `PREVIOUS_SIGHTING_MODIFIED_AT_FILENAME` variable.

> The example script only returns specifically selected fields from each object but can be modified to determine which fields to export.

### Iterating over Flows

In case you need even more granular data, you can also iterate over `Flows` resource:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  https://api.cta.eu.amp.cisco.com/network-behavior-anomaly-detection/customer/{CUSTOMER_ID}/sightings/{SIGHTING_ID}/flows
```

`Flow` is immutable and its' `timeStamp` field indicates when it was observed in the network.

> Beware that there could be a magnitude more of `Flows` than `Sightings`. To get the best value out of Cognitive Intelligence, it's usually better to work with `Alerts`, `ThreatOccurrences` and `Sightings` first.

## References

For more information see:

* Cognitive Intelligence [OpenAPI documentation](https://api.cta.eu.amp.cisco.com/docs/)
* Cognitive Intelligence in [Cisco ScanCenter Administrator Guide](http://www.cisco.com/c/en/us/td/docs/security/web_security/scancenter/administrator/guide/b_ScanCenter_Administrator_Guide/b_ScanCenter_Administrator_Guide_chapter_011110.html)
