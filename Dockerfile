FROM quay.io/edge-infrastructure/assisted-service:latest AS service

FROM registry.access.redhat.com/ubi8/ubi-minimal:8.5

RUN microdnf update -y && microdnf install -y python3 python3-pip && microdnf clean all && python3 -m pip install --upgrade pip
WORKDIR assisted_event_scrape/

COPY requirements.txt .
RUN python3 -m pip install -I --no-cache-dir -r requirements.txt vcversioner

COPY .  .
RUN python3 -m pip install .

ENTRYPOINT ["events_scrape"]
