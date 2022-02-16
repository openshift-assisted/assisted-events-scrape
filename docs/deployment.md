# Deployment

The `assisted-events-scrape` project is composed by two main deployables: `assisted-events-scraper` and `kibana-proxy`.

### assisted-events-scraper

CLI application that runs standalone.

### kibana-proxy

Kibana is exposed through a OAUTH proxy, which authenticates users. Once users are authenticated, Elasticsearch's AWS OpenDistro Dashboard is proxied to the user, where another login is necessary for authorization.
