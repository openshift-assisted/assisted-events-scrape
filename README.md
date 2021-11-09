# assisted-events-scrape

[![License Apache](https://img.shields.io/github/license/openshift/assisted-service)](https://opensource.org/licenses/Apache-2.0)

## About
A little service that publishes the [assisted-service](https://github.com/openshift/assisted-service) cluster events to Elasticsearch.
It pulls all the cluster events and merge it with the existing data.

### Environment variables
| Variable    |  Description   | Example    |
| --- | --- | --- |
| `ES_INDEX`          | Elasticsearch index name | assisted-service-events |
| `LOGS_DEST`          | Logs directory, can be relative |  |
| `ES_SERVER`          | Elasticsearch server address |  |
| `ES_USER(optional)`          | Elasticsearch user name | elastic |
| `ES_PASS(optional)`          | Elasticsearch password  |  |
| `REMOTE_SERVICE_URL` | Assisted service url  | https://api.openshift.com |
| `OFFLINE_TOKEN` | Assisted service offline token  | |
| `INVENTORY_URL` | Assisted service inventory url  | |
| `BACKUP_DESTINATION` | Path to save backup, if empty no backups will be saved  | |
