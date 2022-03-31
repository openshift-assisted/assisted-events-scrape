# Testing

Testing is split into two categories:

* Unit tests
* Integration test

## Unit tests

Unit tests can be run through `make unit-test` (`skipper make unit-test`) command, which will run `pytest`.

## Integration tests

Integration tests need to set up a test environment composed by 3 elements:

* Mock assisted service
* assisted-events-scrape with candidate image
* Elasticsearch server

Once the environment is set up, the scraper will consume all events available from the mock assisted service.
We will then check Elasticsearch (which is exposed through NodePort service) from python tests, located in `tests/integration/`.

### Mock assisted service

Mock assisted service is implemented through [mockserver](https://www.mock-server.com/).
We can easily add mock data through a series of utils scripts: to add a new cluster and its events
to the fixtures, we can just run `./assisted-events-scrape/tests/integration/tools/import_fixture.sh <cluster_id>`. This command will generate
three new files:
* `tests/integration/fixtures/clusters-<cluster_id>.json` - this file will be served as part of the mock endpoint `/v2/clusters` response, as item of the clusters list.
* `tests/integration/fixtures/cluster-<cluster_id>.json` - this file will be served by mock endpoint `/v2/cluster/<cluster_id>`. This endpoint is consumed by `get_cluster_hosts` and other methods.
* `tests/integration/fixtures/events-<cluster_id>.json` - this file will be served by mock endpoint `/v2/events?cluster_id=<cluster_id>`

Another utility is used to then generate mockserver config from the imported fixtures: `tools/generate_mockserver_config.py`

Yet another tool (`tools/generate_mockserver_configmap.sh`) will generate the k8s manifest that can be applied as part of mockserver deployment