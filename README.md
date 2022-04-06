# assisted-events-scrape

[![License Apache](https://img.shields.io/github/license/openshift/assisted-service)](https://opensource.org/licenses/Apache-2.0)

## About
A little service that publishes the [assisted-service](https://github.com/openshift/assisted-service) cluster events to Elasticsearch.
It pulls all the cluster events and merge it with the existing data.

## Install
```bash
make install 
```

## Testing

Documentation about testing can be found [here](docs/testing.md).

## Usage:
This tool can be used by `events_scrape` cli command (if installed) or running using python without installing  using the command: `python3 -m assisted-events-scrape.events_scrape` 

### Environment variables
| Variable    |  Description   | Example    |
| --- | --- | --- |
| `ES_INDEX`              | Elasticsearch index name | assisted-service-events |
| `ES_SERVER`             | Elasticsearch server address |  |
| `ES_USER`(optional)     | Elasticsearch user name | elastic |
| `ES_PASS`(optional)     | Elasticsearch password  |  |
| `ASSISTED_SERVICE_URL`  | Assisted service url  | https://api.openshift.com |
| `OFFLINE_TOKEN`         | Assisted service offline token  | |
| `BACKUP_DESTINATION`    | Path to save backup, if empty no backups will be saved  | |
| `SSO_URL`               | SSO server URL  | |
| `SENTRY_DSN`            | Sentry DSN | |
| `ERRORS_BEFORE_RESTART` | Maximum numbner of errors allowed before restarting the application | |
| `MAX_IDLE_MINUTES`      | Minutes allowed for the application to be idle. Idle time is when the application is not being updated, either succesfully or unsuccesfully | |
| `N_WORKERS`             | Number of workers in the thread pool. Defaults to 5 - minimum 1. | |


### OAuth Proxy Configuration

In order to proxy elasticsearch/kibana, we use [OAuth Proxy](https://github.com/openshift/oauth-proxy) to provide authentication layer.

Below we describe the options that are used:


- `-http-address` The binding address.
- `-provider` OAuth provider. We use `openshift`
- `-openshift-service-account` Service account where `client-id` and `client-secret` will be read from
- `-openshift-sar` [JSON Subject Access Review](https://github.com/openshift/oauth-proxy#require-specific-permissions-to-login-via-oauth-with---openshift-sarjson)
- `-pass-basic-auth` We turn this option off: we just want to proxy provided Basic Auth headers, and not pass authorized user as user
- `-htpasswd-file` htpasswd file path used for authorizing system users
