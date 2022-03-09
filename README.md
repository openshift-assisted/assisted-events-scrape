# assisted-events-scrape

[![License Apache](https://img.shields.io/github/license/openshift/assisted-service)](https://opensource.org/licenses/Apache-2.0)

## About
A little service that publishes the [assisted-service](https://github.com/openshift/assisted-service) cluster events to Elasticsearch.
It pulls all the cluster events and merge it with the existing data.

## Install
```bash
make install 
```


## Usage:
This tool can be used by `events_scrape` cli command (if installed) or running using python without installing  using the command: `python3 -m assisted-events-scrape.events_scrape` 

### Environment variables
| Variable    |  Description   | Example    |
| --- | --- | --- |
| `ES_INDEX`              | Elasticsearch index name | assisted-service-events |
| `ES_SERVER`             | Elasticsearch server address |  |
| `LOGS_DEST`(optional)   | Logs path, can be relative, default to the stdout | assisted-events-scrape.log |
| `ES_USER`(optional)     | Elasticsearch user name | elastic |
| `ES_PASS`(optional)     | Elasticsearch password  |  |
| `ASSISTED_SERVICE_URL`  | Assisted service url  | https://api.openshift.com |
| `OFFLINE_TOKEN`         | Assisted service offline token  | |
| `BACKUP_DESTINATION`    | Path to save backup, if empty no backups will be saved  | |
| `SSO_URL`               | SSO server URL  | |
| `SENTRY_DSN`            | Sentry DSN | |
| `ERRORS_BEFORE_RESTART` | Maximum numbner of errors allowed before restarting the application | |
| `MAX_IDLE_MINUTES`      | Minutes allowed for the application to be idle. Idle time is when the application is not being updated, either succesfully or unsuccesfully | |
