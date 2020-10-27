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

Written in simplified code for alerts it can be logically done like in this javascript snippet:

```javascript
const API_HOST_NAME = 'https://api.cta.eu.amp.cisco.com';
const CUSTOMER_ID = 'YOUR_CUSTOMER_ID';
const ACCESS_TOKEN = 'YOUR_VALID_ACCESS_TOKEN';

let fetchUrl = `/alert-management/customer/${CUSTOMER_ID}/alerts`

async function getAllAlerts() {
    const alerts = [];

    do {
        // request for page of items
        const response = await fetch(`${API_HOST_NAME}${fetchUrl}`, {
            headers: {
                Authorization: `Bearer ${ACCESS_TOKEN}`,
                Accept: 'application/json'
            }
        });
        const data = await response.json();

        // collect all received items together, preserve order
        alerts = [...alerts, ...data.items];

        // set fetchUrl to next page
        fetchUrl = data.pageInfo.next;

        // repeat loop when next page is available
    } while(data.pageInfo.hasNextPage);

    return alerts;
}
```

## References

For more information see:

* Cognitive Intelligence [OpenAPI documentation](https://api.cta.eu.amp.cisco.com/docs/)
* Cognitive Intelligence in [Cisco ScanCenter Administrator Guide](http://www.cisco.com/c/en/us/td/docs/security/web_security/scancenter/administrator/guide/b_ScanCenter_Administrator_Guide/b_ScanCenter_Administrator_Guide_chapter_011110.html)
