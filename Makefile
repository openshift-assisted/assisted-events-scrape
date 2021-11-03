CONTAINER_COMMAND := $(shell ./utils.sh get_container_runtime_command)

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
	$(CONTAINER_COMMAND) build -t assisted-event-scrap .

##########
# Verify #
##########

lint: flake8

flake8:
	flake8 .
