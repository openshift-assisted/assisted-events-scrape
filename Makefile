CONTAINER_COMMAND := $(shell ./tools/utils.sh get_container_runtime_command)
TAG := $(or ${TAG},latest)
ASSISTED_EVENTS_SCRAPE_IMAGE := $(or $(ASSISTED_EVENTS_SCRAPE_IMAGE),quay.io/edge-infrastructure/assisted-events-scrape:$(TAG))
TEST_NAMESPACE := assisted-events-scrape-test

install_assisted_service_client:
	python3 -m pip install assisted-service-client

build-image:
	$(CONTAINER_COMMAND) build $(CONTAINER_BUILD_EXTRA_PARAMS) -t $(ASSISTED_EVENTS_SCRAPE_IMAGE) .

build-wheel:
	rm -rf ./dist ./build
	python3 -m setup bdist_wheel

install: build-wheel
	python3 -m pip uninstall assisted_events_scrape -y
	python3 -m pip install -I dist/assisted_events_scrape-*-py3-none-any.whl


##########
# Verify #
##########

validate-manifest:
	oc process --local=true -f openshift/template.yaml --param IMAGE_TAG=foobar | kubeconform -strict -verbose -

validate-dashboards:
	kubeconform -strict -verbose dashboards/

lint: flake8 pylint

pylint:
	pylint ./assisted-events-scrape

flake8:
	flake8 .

test: validate-manifest lint unit-test cleanup-integration-test integration-test

unit-test:
	pytest assisted-events-scrape/tests/unit

ci-integration-test:
	./tools/deploy_manifests.sh ocp $(ASSISTED_EVENTS_SCRAPE_IMAGE) $(TEST_NAMESPACE)
	./tools/run_integration_test.sh $(TEST_NAMESPACE) ocp

deploy-kind: build-image
	kind get clusters | grep assisted-events-scrape || kind create cluster --name assisted-events-scrape
	kind --name assisted-events-scrape export kubeconfig
	./tools/kind_pull_and_push.sh
	kubectl apply -f .kind/daemonset.yaml
	kind load docker-image --name assisted-events-scrape $(ASSISTED_EVENTS_SCRAPE_IMAGE)
	./tools/deploy_manifests.sh kind $(ASSISTED_EVENTS_SCRAPE_IMAGE) $(TEST_NAMESPACE)

integration-test: deploy-kind
	./tools/run_integration_test.sh $(TEST_NAMESPACE) kind

cleanup-integration-test:
	kind delete cluster --name assisted-events-scrape || true

kind-reload-image: build-image
	kind load docker-image --name assisted-events-scrape $(ASSISTED_EVENTS_SCRAPE_IMAGE)
	kubectl delete pod -l app=assisted-events-scrape

rerun-export-job: kind-reload-image
	kubectl delete job test-s3
	oc create job test-s3 --from=cronjob/ccx-export
