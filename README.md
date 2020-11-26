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

> Script is available in file `get_all_alerts.py`.

## Synchronize Cognitive threat detections to external systems

Cognitive API is also able to offer more granular pieces of detected cyber threat information. In our case
besides `Alerts` we have also on API available lower level `ThreatOccurrences` and `Sightings`.

> When you'd like to know more details about `ThreatOccurrence` or `Sighting` visit our
>[documentation](http://www.cisco.com/c/en/us/td/docs/security/web_security/scancenter/administrator/guide/b_ScanCenter_Administrator_Guide/b_ScanCenter_Administrator_Guide_chapter_011110.html)
>.

Each object has its own collection able to go through all items available. Collection resources are paged by default.

### Resources to access ThreatOccurrences and Sightings

To get first page of `ThreatOccurrences` you can use following query:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  https://api.cta.eu.amp.cisco.com/threat-detection/customer/{CUSTOMER_ID}/threat-occurrences
``` 

To get first page of `Sightings` you can use following query:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  https://api.cta.eu.amp.cisco.com/network-behavior-anomaly-detection/customer/{CUSTOMER_ID}/sightings
``` 

On each `Sighting` there could be available field `securityAnnotaton` which represents key observations which
was identified and was used for detecting threat or malicious behaviour.
When `securityAnnotaton` is not available event classification - property `eventTypeId` - should be available by
default.

### Iterate over Sightings hierarchically with Alert and ThreatOccurrence in context

To put everything together you need to start from `Alerts` as mentioned above. Then you need to go through all
`ThreatOccurrences` belonging to each `Alert` and then you need to go through all convicting `Sightings`
of each `ThreatOccurrence` and process their content.

> Optionally you can also go through all contextual `Sightings` to get better insight using resource
> `/threat-detection/customer/{CUSTOMER_ID}/threat-occurrences/{THERAT_OCCURRENCE_ID}/sightings/contextual` but
> you need to be careful. Each contextual `Sighting` spotted for particular `Asset` belongs to every
> `ThreatOccurrence` detected for this `Asset`. Is quite common one contextual `Sighting` belongs to several
> `ThreatOccurrences`. So you need to avoid multiple processing.

To understand better look at following python code snippet:

> You have here available `CollectionIterator`, class implementing `has_next` and `next` methods able to go through all 
> pages of items of each individual collection. `CollectionIterator` class is available in file `get_security_annotations.py`

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
Imagine `process_sighting` is a method processing each `Sighting` - here together with the parent - `ThreatOccurrence`
object and with `ThreatOccurrence`'s parent `Alert`.

> One convicting `Sighting` can belong to one or more `ThreatOccurrences` but relation to more `ThreatOccurrences` is rare.
> So for simplification we ignore duplicities.

#### Repeated iterations over Sightings

To automate process of working with `Sightings`, e.g. for importing to SIEM you mostly need to process
only new or updates `Sightings`. Each `Sighting` (and `ThreatOccurrence`) has two date fields 
available:
- `detectedAt` - instant when this entity was created by anomaly classification engine
- `modifiedAt` - instant when this entity was last updated by anomaly classification engine

More suitable for us is `modifiedAt` because `Sighting` is not immutable and can be changed over time.

When we are running first iteration over `Sightings` important for next round of iteration is thus `modifiedAt`
attribute, especially maximum `modifiedAt` value across all `Sightings`.
When I repeat iteration I can simply compare each `Sighting.modifiedAt` with maximum `modifiedAt` from previous
run and I can process only new or updated `Sightings`. 

Because `Sightings` observables are aggregated we cannot distinguish between old attributes and new attrributes
and you have to process it as a bulk.

> In case you need even more granular items you can to iterate over `Flows` resource
> `/network-behavior-anomaly-detection/customer/{CUSTOMER_ID}/sightings/{SIGHTING_ID}/flows`.
> `Flow` item is immutable and `timeStamp` fields indicates when this item was observed in network. 
> But there could be potentially magnitude more of `Flows` than `Sightings` so we prefer working
> with `Sightings`.


### Import Sightings to Splunk

With the previous code and knowledge we are now able to write script to process `Sightings` to Splunk.
Working example is available in script `get_security_annotations.py`. You can use it as a template
for your own script. You need Python 2.7+ to run the code.

You need to modify it and enter into script your:
* `CUSTOMER_ID`
* valid `ACCESS_TOKEN`
* when running in Splunk also full path to file in `PREVIOUS_SIGHTING_MODIFIED_AT_FILENAME`.

> With correctly filled in access info you can verify script output locally. 

Script after every run persists maximal `modifiedAt` across all processed `Sightings`. When you'd like to run full
processing again delete file specified in `PREVIOUS_SIGHTING_MODIFIED_AT_FILENAME` variable. If you'd like to 
store this file elsewhere, e.g. due to permissions, modify value of this variable according your needs.

Script output is generated in `log_sighting_attributes` method and is in JSON. You can use Splunk pre-defined
source type `_json` to process output from the script. You can also modify what is being exported. You can add
other fields or remove existing ones.

## References

For more information see:

* Cognitive Intelligence [OpenAPI documentation](https://api.cta.eu.amp.cisco.com/docs/)
* Cognitive Intelligence in [Cisco ScanCenter Administrator Guide](http://www.cisco.com/c/en/us/td/docs/security/web_security/scancenter/administrator/guide/b_ScanCenter_Administrator_Guide/b_ScanCenter_Administrator_Guide_chapter_011110.html)
