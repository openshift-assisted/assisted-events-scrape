CONTAINER_COMMAND := $(shell ./tools/utils.sh get_container_runtime_command)
IMAGE_TAG := $(or ${IMAGE_TAG}, latest)
IMAGE_NAME := $(or $(ASSISTED_EVENTS_SCRAPE_IMAGE),quay.io/edge-infrastructure/assisted-events-scrape)
ASSISTED_EVENTS_SCRAPE_IMAGE := $(IMAGE_NAME):$(IMAGE_TAG)

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

lint: flake8 pylint

pylint:
	pylint ./assisted-events-scrape

flake8:
	flake8 .

test: lint unit-test cleanup-integration-test integration-test

unit-test:
	pytest assisted-events-scrape/tests/unit

integration-test: build-image
	kind get clusters | grep assisted-events-scrape || kind create cluster --name assisted-events-scrape
	kind --name assisted-events-scrape export kubeconfig
	kind load docker-image --name assisted-events-scrape $(ASSISTED_EVENTS_SCRAPE_IMAGE)
	./tools/generate_mockserver_configmap.sh | kubectl delete -f - || true
	./tools/generate_mockserver_configmap.sh | kubectl create -f - || true
	kubectl apply -f assisted-events-scrape/tests/integration/manifests
	kubectl wait --timeout=120s --for=condition=Available deployment --all
	kubectl wait --timeout=300s --for=condition=Ready pods --all
	./tools/ocp2k8s.sh $(ASSISTED_EVENTS_SCRAPE_IMAGE) | kubectl apply -f -
	kubectl wait --timeout=30s --for=condition=Available deployment --all
	kubectl wait --timeout=30s --for=condition=Ready pods --all
	ES_SERVER=$$(./tools/get_elasticsearch_endpoint.sh) ES_INDEX=assisted-service-events pytest assisted-events-scrape/tests/integration

cleanup-integration-test:
	kind delete cluster --name assisted-events-scrape || true
