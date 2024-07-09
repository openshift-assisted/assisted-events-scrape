FROM registry.access.redhat.com/ubi9/ubi-minimal:9.2

RUN microdnf update -y && microdnf install -y python3 python3-pip && python3 -m pip install --upgrade pip
WORKDIR assisted_event_scrape/

COPY requirements.txt .
RUN python3 -m pip install -I -r requirements.txt vcversioner

COPY . .
RUN python3 -m pip install .

ENTRYPOINT ["events_scrape"]
