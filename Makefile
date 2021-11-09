CONTAINER_COMMAND := $(shell ./utils.sh get_container_runtime_command)
TAG := $(or ${TAG},latest)
ASSISTED_EVENTS_SCRAPE_IMAGE := $(or $(ASSISTED_EVENTS_SCRAPE_IMAGE),quay.io/edge-infrastructure/assisted-events-scrape:$(TAG))

install_assisted_service_client:
	$(eval container_id := $(shell docker create quay.io/ocpmetal/assisted-service))
	rm -rf build/pip/assisted-service-client
	mkdir -p build/pip/assisted-service-client/
	docker cp $(container_id):/clients/. build/pip/assisted-service-client/
	ls -1  build/pip/assisted-service-client/*.tar.gz
	docker rm -v $(container_id)
	python3 -m pip install `ls build/pip/assisted-service-client/*`
	rm -rf build

build-image:
	$(CONTAINER_COMMAND) build -t $(ASSISTED_EVENTS_SCRAPE_IMAGE) .

##########
# Verify #
##########

lint: flake8

flake8:
	flake8 .
