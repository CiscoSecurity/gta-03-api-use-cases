# Using Global Threat Alerts (formerly Cognitive Intelligence) API

To access global threat alerts API, you need to have enabled integration with Cognitive Threat Response/SecureX
and valid SecureX API client credentials. You can find information on creating it
in [Getting API Access Token](https://api.cta.eu.amp.cisco.com/docs/#/authentication) global threat alerts documentation.
Specifically you'll need:
* Client ID (`SECUREX_CLIENT_ID`)
* Client Password (`SECUREX_CLIENT_PASSWORD`)
* Regional API endpoint (`SECUREX_VISIBILITY_HOST_NAME`)

Most resources require you to know your `CUSTOMER_ID`. You can find it in [UI](https://cognitive.cisco.com/ui) under
the user icon in the main navigation.

## Authentication

When you have available SecureX client ID (`SECUREX_CLIENT_ID`), password (`SECUREX_CLIENT_PASSWORD`), and regional
API endpoint (`SECUREX_VISIBILITY_HOST_NAME`) you can now ask for token:

```console
$ curl -X POST \
     -u "${SECUREX_CLIENT_ID}:${SECUREX_CLIENT_PASSWORD}" \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -H 'Accept: application/json' \
     -d 'grant_type=client_credentials' \
  "https://${SECUREX_VISIBILITY_HOST_NAME}/iroh/oauth2/token"
```

You'll get the token response (200 OK):
```json
{
    "access_token": "ey..this.is.very.long.in.reality.....example..Eg",
    "token_type": "bearer",
    "expires_in": 600,
    "scope": "casebook"
}
```
In case something went wrong you'll get "400 Bad Request" with explanation in "error_description",
e.g. for invalid client ID:
```json
{
    "error": "invalid_client",
    "error_description": "unknown client",
    "error_uri": "https://tools.ietf.org/html/rfc6749#section-5.2"
}
```

To construct authorization header (in form `Authorization: <type> <credentials>`) you need to combine information
from `token_type` and `access_token`. We do translate `"token_type": "bearer"` to type `Bearer` and use `access_token`
value as credentials.

For examples used in the rest of the document, we store `access_token` response value to `ACCESS_TOKEN` variable.

> Numeric value in `expires_in` shows us current token validity - this one is valid for 600 seconds (10 minutes).
> You need to refresh the token before it expires, otherwise you'll get "401 Unauthorized" response.

## Basic usage

Use the `/alerts` resource to get `Alerts`:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts"
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

### Get new Alerts triggered after the last synchronization

For initial synchronization of `Alerts`, use the `/alerts` resource with `sort=triggeredAt:asc` parameter:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts?sort=triggeredAt:asc"
```

To get only newly created `Alerts` in subsequent synchronizations:

1. take `triggeredAt` of last `Alert` from previous request (it's the latest because of `sort=triggeredAt:asc`)
1. use it for new request as a `triggeredAfter` parameter

Example:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts?triggeredAfter=2020-09-05T12:00:00Z&sort=triggeredAt:asc"
```

See [Date-time format](#date-time-format) for more information about `triggeredAfter` format.

### Get modified (and new) Alerts after a specific point in time

Use the `/alerts` resource with `modifiedAfter=[date-time]` parameter:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts?modifiedAfter=2024-09-05T12:00:00Z"
```
You'll get all `Alerts` with `Alert.modifiedAt` value greater than value requested in `modifiedAfter` parameter.

See [Date-time format](#date-time-format) for more information about `modifiedAfter` format.

`Alert.modifiedAt` is initially the same as `Alert.triggeredAt` but changes when:

* The `Alert` content changes (eg. `risk`, `state`, `etaFlag`, `note`).
* `ThreatDetection` is added to the `Alert`.
* `ThreatDetection` is removed from the `Alert`.

### Synchronize previously saved Alerts one by one

To synchronize `Alerts` you already requested before you have these options:

* Repeat the original request to get all the `Alerts`.
* Query saved alerts one by one. If alert was removed you'll get `404 Not Found` as a response.

> `Alert` is removed when all its related `ThreatDetection`s time out.
> `ThreatDetection` times out after 45 days since its latest detected malicious activity.

## Get a single Alert

To get one Alert with a known `id`, use:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts/${ALERT_ID}"
```

## Update Alert state

To change Alert state, use:

```console
$ curl -X PATCH \
       -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
       -H "Content-Type: application/json" \
       --data '{"state":"Remediated"}' \
  "https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts/${ALERT_ID}/state"
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
  "https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts/${ALERT_ID}/note"
```

_**Caution:** When the alert is in the New state, the note may get deleted when alerts are recalculated. To prevent this, change the state of the alert to not New._

> To remove note call `DELETE` method on `/note` resource.

## Date-time format

For parameters like `triggeredAfter`, `modifiedAfter`, etc. use ISO 8601 date-time format as defined by [RFC 3339, section 5.6](https://tools.ietf.org/html/rfc3339#section-5.6).

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
  * a relative path to the previous page
  * if the previous page does not exist or request method is POST, `null` is returned
* `next`
  * a relative path to the next page
  * if the next page does not exist or request method is POST, `null` is returned.
* `hasPreviousPage` 
  * boolean value about the previous page existence
  * `true` means the previous page is available
* `hasNextPage`
  * boolean value about the next page existence
  * `true` means the next page is available
* `startCursor`
  * value identifies the first item in the current results
  * should be used to construct a request for the previous page. Necessary when requesting collection resources with parameters using POST method. 
  * when the previous page is not available, `null` is returned
* `endCursor`
  * value identifies the last item in the current results
  * should be used to construct a request for the next page. Necessary when requesting collection resources with parameters using POST method.
  * when the next page is not available, `null` is returned

### Limiting results

To limit how many items should be returned, use `size=[number]` query string parameter.

Maximum number of requested items is `1,000`.

> This limit is also applied when requesting collection without the `size` parameter.

Example:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts?size=10"
```

### Getting the next page

To get the next page of previous response, use `after=[endCursor]` query parameter in your next request:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/alert-management/customer/CTA123456789/alerts?size=10&after=32c43ccb-20b7-4e39-a2ab-d05791ae23f0"
```

> You can also use the `next` link from the `pageInfo` if available.

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

> This script improved by direct usage of SecureX credential is available in the `get_all_alerts.py` file. 

## Synchronizing external SIEM

In addition to `Alerts`, Global Threat Alerts API also offers more granular information like `ThreatDetections` or `Events`.

> Learn more about `ThreatDetection` and `Event` in
>[Global Threat Alerts Documentation](https://www.cisco.com/c/en/us/td/docs/security/cognitive/cognitive-intelligence-user-guide/m_dashboard.html)
>.

To get the first page of `ThreatDetections`, use the following query:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/threat-detection/customer/${CUSTOMER_ID}/threat-detections"
```

To get the first page of security `Events`:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/event-detection/customer/${CUSTOMER_ID}/events"
```

### Modification Sequence Number

Because there are potentially a lots of `ThreatDetections` and magnitude more `Events` we need to have mechanism
how to get from API just new or updated items. We usually don't want to deal with e.g., all `Events` again when
we already processed and synchronized part of them. Previously we introduced time based query parameters,
especially on `Alert` level but such approach is not suitable here because in one moment lots of objects can be created.
And yes, we can miss some important ones when relying just on time.

For stable order of items returned in response we implemented `modification sequence number` mechanism.
`Modification sequence number` is unique increasing number which is internally assigned to all `Events`, `ThreatDetections`
and `Flows` when they are created or re-assigned when objects are updated. `modification sequence numbers`
are only available in collection responses in `pageInfo`section for first and last item as `startCursor` and `endCursor` values.
You only need to query collection with specific sort parameter`sort=modificationSequenceNumber` to get them.
Such stable order of items in collection ensure we do not miss any important update and we can safely continue where we ended last time.

> Only selected resources support `sort=modificationSequenceNumber`,
> see Global Threat Alerts [OpenAPI documentation](https://api.cta.eu.amp.cisco.com/docs/) which resources are supported.

See how we can use `sort=modificationSequenceNumber` on `/events/search` resource:

```console
$ curl -X POST \
       -d '{"filter": {}}' \
       -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
       -H "Content-Type: application/json" \
  "https://api.cta.eu.amp.cisco.com/event-detection/customer/${CUSTOMER_ID}/events/search?sort=modificationSequenceNumber"
```

The last paged response could be:

```jsonc
    {
      "items": [ /* array */ ],
      "pageInfo": {
        "previous": null,
        "next": null,
        "hasNextPage": false,
        "hasPreviousPage": true,
        "startCursor": "25716998",
        "endCursor": "25717281"
      }
    }
```

When e.g., next day we would like to get just increments, (new and updated) `Events` we need to remember `endCursor`
value of the response (`25717281`) and repeat the query with `after` query parameter having `endCursor` as value (`after=25717281`):

```console
$ curl -X POST \
       -d '{"filter": {}}' \
       -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
       -H "Content-Type: application/json" \
  "https://api.cta.eu.amp.cisco.com/event-detection/customer/${CUSTOMER_ID}/events/search?sort=modificationSequenceNumber&after=25717281"
```
> See [Getting the next page](#getting-the-next-page) for more details about how to work with `pageInfo` object

### Iterating over Events hierarchically with an Alert and a ThreatDetection in the context

To put everything together:

1. Iterate over all `Events` with `modificationSequenceNumber` stable sort (as described in previous sections) 
   having reference to parent `ThreatDetections`. There is special resource for this purpose
   `/threat-detection/customer/${CUSTOMER_ID}/enriched-events-with-threat-detection-ids`.
1. Get all referred `ThreatDetections` with references to `Alerts`.
   Use `/alert-management/customer/${CUSTOMER_ID}/enriched-threat-detections-with-alert-ids/search` 
1. You can get `Alerts` one by one or use bulk resource to get them.
   E.g., `/alert-management/customer/${CUSTOMER_ID}/alerts/search`

> `Events` without references to `ThreatDetections` are called "contextual" while `Events` with reference(s) are called "convicting".

#### Example (simplified)

Following example explains how to traverse objects from bottom to top, from `Events` to `Alerts`. It shows how to use 
performance optimized resources and for simplification some parts like authorization are omitted.
Approach described in this example is used in `get_security_annotations.py` file - when you'd like to try it out 
start with this script file.

```python
CUSTOMER_ID = "YOUR_CUSTOMER_ID"

def start():
    events = []
    threat_detection_ids = []
    alert_ids = []
    cached_context_objects = {}

    # get all Events in stable order ensured by `modificationSequenceNumber` 
    events_iterator = CollectionIterator(
        collection_url_path="/threat-detection/customer/" + CUSTOMER_ID + "/enriched-events-with-threat-detection-ids",
        query_params={
            "sort": "modificationSequenceNumber",
        })

    # extract references to threat detections and keep them for final processing
    while events_iterator.has_next():
        event = events_iterator.next()
        events.append(event)
        threat_detection_ids.extend(event["threatDetectionIds"])

    # bulk load threat detections
    threat_detections_iterator = CollectionIterator(
        collection_url_path="/alert-management/customer/" + CUSTOMER_ID + "/enriched-threat-detections-with-alert-ids/search",
        request_body={
            "filter": {
                "threatDetectionIds": list(set(threat_detection_ids))
            }
        })

    # extract references to alerts and keep threat detections in cache key=ID, value=OBJECT
    while threat_detections_iterator.has_next():
        threat_detection = threat_detections_iterator.next()
        cached_context_objects[threat_detection["id"]] = threat_detection
        alert_ids.extend(threat_detection["alertIds"])

    # bulk load alerts
    alerts_iterator = CollectionIterator(
        collection_url_path="/alert-management/customer/" + CUSTOMER_ID + "/alerts/search",
        request_body={
            "filter": {
                "alertIds": list(set(alert_ids))
            }
        })

    # keep alerts in cache key=ID, value=OBJECT
    while alerts_iterator.has_next():
        alert = alerts_iterator.next()
        cached_context_objects[alert["id"]] = alert

    # Process
    for event in events:
        # get IDs references to threat detections from event (usually one)
        threat_detection_ids = event["threatDetectionIds"]
    
        # process all possible threat detections
        if len(threat_detection_ids) > 0:
            # process event with threat detections (called "convicting" security event)
            for threat_detection_id in threat_detection_ids:
                # get parent objects to event - threat detections and alert
                threat_detection_with_alert_ids = cached_context_objects[threat_detection_id]
    
                # get IDs references to alerts (usually one)
                alert_ids = threat_detection_with_alert_ids["alertIds"]
                for alert_id in alert_ids:
                    alert = cached_context_objects[alert_id]
    
                    # log event with related objects - alert, threat detection
                    log_event_attributes(event, threat_detection_with_alert_ids, alert)
        else:
            # process event without threat detections (called "contextual" security event)
            log_event_attributes(event)
```

> `CollectionIterator` class is available in the `api_client.py` file. It implements `has_next` and `next` methods
> to be able to go through all pages of items of each individual collection.
> In real usage you also need to provide `authorization_fn` argument - function able to provide on demand authorization header value.

Method `log_event_attributes` represents whatever processing of `Event` you wish to do, with access to the parent `ThreatDetection` and its parent `Alert`.

#### Repeated iterations over Events

You just need to remember events `endCursor` - available under `events_iterator.end_cursor` in previous script example and use it next time as `cursor` argument when
constructing `CollectionIterator`:

```python
    events_iterator = CollectionIterator(
        collection_url_path="/threat-detection/customer/" + CUSTOMER_ID + "/enriched-events-with-threat-detection-ids",
        query_params={
            "sort": "modificationSequenceNumber",
        },
        cursor=previous_events_end_cursor
    )
```

> Because `Event` observables are aggregated, it's not possible to distinguish between old attributes values and new ones inside `Event`. `Event` needs to be processed as a whole.

### Importing Events to Splunk

Working example script is available in the  `get_security_annotations.py` file. It can be used as a template for writing more complex scripts.

> Python 2.7+ is required to run the code.

To get started, modify the example script and provide your:

* valid SecureX credentials - `SECUREX_CLIENT_ID` and `SECUREX_CLIENT_PASSWORD`
* SecureX visibility host name - `SECUREX_VISIBILITY_HOST_NAME`
* full path to the file in `EVENTS_END_CURSOR_FILENAME`

The script output is generated in `log_event_attributes` method and it's in JSON format. Use Splunk's pre-defined
source type `_json` to process output of the script.

After each run, the example script persists last processed event `endCursor` to file `EVENTS_END_CURSOR_FILENAME`.

To run full processing again, delete the file specified in the `EVENTS_END_CURSOR_FILENAME` variable.

> The example script only returns specifically selected fields from each object but can be modified to determine which fields to export.

### Iterating over Flows

In case you need even more granular data, you can also iterate over `Flows` resource:

```console
$ curl -X POST
       -d '{"filter": {}}'
       -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/event-detection/customer/${CUSTOMER_ID}/flows/search?sort=modificationSequenceNumber"
```

`Flow` is immutable and its' `timeStamp` field indicates when it was observed in the network.
`Flows` also support modification sequence number stable sort.

> Beware that there could be a magnitude more of `Flows` than `Events`.
> To get the best value out of Global Threat Alerts, it's usually better to work with `Alerts`, `ThreatDetections` and `Events` first.

## References

For more information see:

* Global Threat Alerts [OpenAPI documentation](https://api.cta.eu.amp.cisco.com/docs/)
* Global Threat Alerts in [Cisco Global Threat Alerts User Guide](https://www.cisco.com/c/en/us/td/docs/security/cognitive/cognitive-intelligence-user-guide/m_dashboard.html)
