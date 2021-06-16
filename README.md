# Using Global Threat Alerts (formerly Cognitive Intelligence) API

To access the global threat alerts API, you must link your global threat alerts customer identity with SecureX and create a SecureX API Client. You can find detailed instructions in global threat alerts documentation on the [Getting API Access Token](https://api.cta.eu.amp.cisco.com/docs/#/authentication) page.

To continue, you'll need:

* Client ID (`SECUREX_CLIENT_ID`)
* Client Password (`SECUREX_CLIENT_PASSWORD`)
* Regional API endpoint (`SECUREX_VISIBILITY_HOST_NAME`)

Most resources require you to know your `CUSTOMER_ID`. You can find it in the [Cisco Global Threat Alerts UI](https://cognitive.cisco.com/ui), under the user icon in the main navigation.

## Authentication

Use SecureX Client ID (`SECUREX_CLIENT_ID`), password (`SECUREX_CLIENT_PASSWORD`), and regional API endpoint (`SECUREX_VISIBILITY_HOST_NAME`) to acquire global threat alerts API access token:

```console
$ curl -X POST \
     -u "${SECUREX_CLIENT_ID}:${SECUREX_CLIENT_PASSWORD}" \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -H 'Accept: application/json' \
     -d 'grant_type=client_credentials' \
  "https://${SECUREX_VISIBILITY_HOST_NAME}/iroh/oauth2/token"
```

You should get a token response (200 OK):

```json
{
    "access_token": "this_is_an_example_of_a_token",
    "token_type": "bearer",
    "expires_in": 600,
    "scope": "casebook"
}
```

In case something went wrong, you should get a "400 Bad Request" response code with an explanation in "error_description", e.g. for an invalid client ID:

```json
{
    "error": "invalid_client",
    "error_description": "unknown client",
    "error_uri": "https://tools.ietf.org/html/rfc6749#section-5.2"
}
```

When calling global threat alerts API, use the `access_token` value in the `Authorization` header as follows:

```console
Authorization: Bearer <access_token>
```

> Beware that the token type must be capitalized in the `Authorization` header, so the `token_type` value can't be used from the token response directly.

The numeric value in `expires_in` indicates the token validity. Each new token is valid for 600 seconds (10 minutes). You'll need to refresh the token yourself before it expires, otherwise you'll start getting "401 Unauthorized" responses.

For examples used in the rest of this document, we store `access_token` response value as a `ACCESS_TOKEN` variable.

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

1. Take `triggeredAt` of the last `Alert` from the previous API response (this `Alert` is the latest because of `sort=triggeredAt:asc`).
1. Use this `triggeredAt` value for the next request as a `triggeredAfter` parameter.

Example:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts?triggeredAfter=2020-09-05T12:00:00Z&sort=triggeredAt:asc"
```

See [Date-time format](#date-time-format) for more information about the `triggeredAfter` format.

### Get modified (and new) Alerts after a specific point in time

Use the `/alerts` resource with `modifiedAfter=[date-time]` parameter:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts?modifiedAfter=2024-09-05T12:00:00Z"
```

You'll get all `Alerts` with the `Alert.modifiedAt` value greater than the value requested in the `modifiedAfter` parameter.

See [Date-time format](#date-time-format) for more information about the `modifiedAfter` format.

`Alert.modifiedAt` is initially the same as `Alert.triggeredAt`, but changes when:

* The `Alert` content changes (eg. `risk`, `state`, `etaFlag`, `note`).
* `ThreatDetection` is added to the `Alert`.
* `ThreatDetection` is removed from the `Alert`.

### Synchronize previously saved Alerts one by one

To synchronize `Alerts` you already requested before, you have these options:

* Repeat the original request to get all the `Alerts`.
* Query saved alerts one by one. If the alert has been removed, you'll get `404 Not Found` as a response.

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

To change the Alert state, use:

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

> To reset the Alert state back to `New`, you can also call the `DELETE` method on the `/state` resource.

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

> To remove the Alert note, call the `DELETE` method on the `/note` resource.

## Date-time format

For parameters that accept date and time (`triggeredAfter`, `modifiedAfter`, etc.), use the ISO 8601 date-time format as defined by [RFC 3339, section 5.6](https://tools.ietf.org/html/rfc3339#section-5.6).

Same format is also used for all date-time information in the API responses.

> On Unix system, you can use `date -u -v-45d +"%Y-%m-%dT%H:%M:%SZ"` to get the date of 45 days in the past in the correct format.

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
  * if the previous page does not exist or the request method is POST, `null` is returned
* `next`
  * a relative path to the next page
  * if the next page does not exist or the request method is POST, `null` is returned.
* `hasPreviousPage`
  * a boolean value indicating existence of a previous page
  * `true` means the previous page is available
* `hasNextPage`
  * a boolean value indicating existence of a next page
  * `true` means the next page is available
* `startCursor`
  * value identifies the first item in the current results
  * should be used to construct a request for the previous page. Necessary when requesting a collection resources with parameters using the POST method.
  * when the previous page is not available, `null` is returned
* `endCursor`
  * value identifies the last item in the current results
  * should be used to construct a request for the next page. Necessary when requesting a collection resources with parameters using the POST method.
  * when the next page is not available, `null` is returned

### Limiting results

To limit, how many items should be returned, use `size=[number]` query string parameter.

Maximum number of requested items is `1,000`.

> This limit is also applied when requesting a collection without the `size` parameter.

Example:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/alert-management/customer/${CUSTOMER_ID}/alerts?size=10"
```

### Getting the next page

To get the next page of for a previous response, use `after=[endCursor]` query parameter in your next request:

```console
$ curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
  "https://api.cta.eu.amp.cisco.com/alert-management/customer/CTA123456789/alerts?size=10&after=32c43ccb-20b7-4e39-a2ab-d05791ae23f0"
```

> You can also use the `next` link from the `pageInfo` if available.
> Similarly, you can use `previous` link or `before=[startCursor]` parameter to get the previous page.

### Getting all items

To get all collection items, call `next` page URLs from the previous responses until next page is not available (`hasNextPage=false`).

For alerts, written as a simplified python code snippet, it can be done for example like this:

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

> More complete version of this script is available in the `get_all_alerts.py` file.

## Synchronizing external SIEM

In addition to `Alerts`, global threat alerts API also offers more granular information like `ThreatDetections` or `Events`.

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

### Using Modification Sequence Number

In general, there can be a lot of `ThreatDetections`, and an order of magnitude more `Events`. However, for any subsequent SIEM synchronizations (after the initial one), you are probably interested only in new and updated items, not the already processed ones.

In the [previous section](#Synchronizing-external-SIEM), we have introduced time based query parameters, but such an approach is not always suitable. Especially on `Event` level, many objects can get created at one moment. When this happens, you could even miss some important ones, when relying just on the time. To solve this, you can use the modification sequence number mechanism provided by the API.

Modification sequence number is a unique increasing number which is assigned to all `Events`, `ThreatDetections` and `Flows` as they are created, and is re-assigned when these objects are updated.

Modification sequence number allows to achieve a stable order of items in the API responses, so you won't miss any important update. You can safely continue loading more data, starting from the last item you've loaded in the previous synchronization.

To use modification sequence number, set the sort parameter to `sort=modificationSequenceNumber`. Modification sequence numbers will become available in collection responses in `pageInfo` section, for the first and the last items as `startCursor` and `endCursor` values.

> Only selected resources support `sort=modificationSequenceNumber`. Visit global threat alerts [OpenAPI documentation](https://api.cta.eu.amp.cisco.com/docs/) to see which resources are supported.

Assuming the initial synchronization request looks like this:

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
        "endCursor": "25717281" /* modification sequence number */
      }
    }
```

For the next synchronization (e.g. the next day), you would like to get just the increments (new and updated `Events`). Recall `endCursor`
value from the previous response and repeat the query with `after` query parameter having `endCursor` as a value (`after=25717281`):

```console
$ curl -X POST \
       -d '{"filter": {}}' \
       -H "Authorization: Bearer ${ACCESS_TOKEN}" \
       -H "Accept: application/json" \
       -H "Content-Type: application/json" \
  "https://api.cta.eu.amp.cisco.com/event-detection/customer/${CUSTOMER_ID}/events/search?sort=modificationSequenceNumber&after=25717281"

```

> See [Getting the next page](#getting-the-next-page) for more details about how to work with the `pageInfo` object.

### Iterating over Events hierarchically with an Alert and a ThreatDetection in the context

To put everything together:

1. Iterate over all `Events` with the `modificationSequenceNumber` stable sort (as described in the [previous section](#Using-Modification-Sequence-Number)). You can use a special resource for this purpose
   `/threat-detection/customer/${CUSTOMER_ID}/enriched-events-with-threat-detection-ids`, that returns objects that contain references to parent `ThreatDetections`.
1. To get all referred `ThreatDetections`, use `/alert-management/customer/${CUSTOMER_ID}/enriched-threat-detections-with-alert-ids/search` resource. This resource returns objects that contain references to parent `Alerts`.
1. Get all referred `Alerts`, either one by one, or use a bulk resource `/alert-management/customer/${CUSTOMER_ID}/alerts/search`.

> `Events` with references to `ThreatDetections` are called "convicting". `Events` without references to `ThreatDetections` are called "contextual".

The following example explains how to traverse objects from bottom (`Events`) to top (`Alerts`). It also demonstrates how to use performance optimized resources.

For simplification, some parts are omitted.

> The approach described in this example is used in the `get_security_annotations.py` file.

```python
from api_client import ApiClient

CUSTOMER_ID = "YOUR_CUSTOMER_ID"

def start():
    api_client = ApiClient(SECUREX_VISIBILITY_HOST_NAME, SECUREX_CLIENT_ID, SECUREX_CLIENT_PASSWORD)
    events = []
    threat_detection_ids = []
    alert_ids = []
    cached_context_objects = {}

    # get all Events in stable order ensured by `modificationSequenceNumber` 
    events_iterator = api_client.create_collection_iterator(
        collection_url_path="/threat-detection/customer/" + CUSTOMER_ID + "/enriched-events-with-threat-detection-ids",
        query_params={
            "sort": "modificationSequenceNumber",
        })

    # extract references to threat detections and keep them for final processing
    for event in events_iterator:
        events.append(event)
        threat_detection_ids.extend(event["threatDetectionIds"])

    # bulk load threat detections
    threat_detections_iterator = api_client.create_collection_iterator(
        collection_url_path="/alert-management/customer/" + CUSTOMER_ID + "/enriched-threat-detections-with-alert-ids/search",
        request_body={
            "filter": {
                "threatDetectionIds": list(set(threat_detection_ids))
            }
        })

    # extract references to alerts and keep threat detections in cache key=ID, value=OBJECT
    for threat_detection in threat_detections_iterator:
        cached_context_objects[threat_detection["id"]] = threat_detection
        alert_ids.extend(threat_detection["alertIds"])

    # bulk load alerts
    alerts_iterator = api_client.create_collection_iterator(
        collection_url_path="/alert-management/customer/" + CUSTOMER_ID + "/alerts/search",
        request_body={
            "filter": {
                "alertIds": list(set(alert_ids))
            }
        })

    # keep alerts in cache key=ID, value=OBJECT
    for alert in  alerts_iterator:
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

> The `ApiClient` class is available in the `api_client.py` file. It helps you with authorization when accessing 
> the API. It also implements `CollectionIterator` class which is `iterable` and which helps you to traverse through all the
> pages of each individual collection. Use `create_collection_iterator` method on `ApiClient` instance to create 
> `CollectionIterator` instance - it passes to it configured "self" (ApiClient) instance directly.
> In the real world usage, you also need to provide the valid SecureX API host name and client credentials as `ApiClient` arguments.

The `log_event_attributes` method represents whatever processing of the `Event` you would like to do, with the access to the parent `ThreatDetection` and its parent `Alert`.

#### Repeated iterations over Events

For any repeated iterations over `Events`, persist the value of the `endCursor` (available under `events_iterator.end_cursor()` in the previous example), and use it next time as a `cursor` argument value when constructing `CollectionIterator`:

```python
    events_iterator = ApiClient.CollectionIterator(
        collection_url_path="/threat-detection/customer/" + CUSTOMER_ID + "/enriched-events-with-threat-detection-ids",
        query_params={
            "sort": "modificationSequenceNumber",
        },
        cursor=previous_events_end_cursor
    )
```

> Because `Events` are technically aggregated objects, it's not possible to distinguish between old attributes values and new ones inside the `Event`. `Event` needs to be processed as a whole.

### Importing Events to Splunk

Working example script is available in the  `get_security_annotations.py` file. It can be used as a template for writing more complex scripts.

> Python 2.7+ is required to run the code.

To get started, modify the example script and provide your:

* valid SecureX credentials - `SECUREX_CLIENT_ID` and `SECUREX_CLIENT_PASSWORD`
* SecureX visibility host name - `SECUREX_VISIBILITY_HOST_NAME`
* full path to the file in `EVENTS_END_CURSOR_FILENAME`

The script output is generated in the `log_event_attributes` method and it's in JSON format. Use Splunk's pre-defined source type `_json` to process the output of the script.

After each run, the example script persists the `endCursor` of the last processed event to a file defined in the `EVENTS_END_CURSOR_FILENAME` variable.

To run full processing again, delete the file specified in the `EVENTS_END_CURSOR_FILENAME` variable.

> The example script only returns specifically selected fields from each object, but can be modified to determine which fields to export.

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

> Beware that there could be a magnitude more of `Flows` than `Events`. To get the best value out of global threat alerts, it's usually better to work with `Alerts`, `ThreatDetections`, and `Events` first.

## References

For more information see:

* Cisco global threat alerts [OpenAPI documentation](https://api.cta.eu.amp.cisco.com/docs/)
* Cisco global threat alerts in [Cisco Global Threat Alerts User Guide](https://www.cisco.com/c/en/us/td/docs/security/cognitive/cognitive-intelligence-user-guide/m_dashboard.html)
