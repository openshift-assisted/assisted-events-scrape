FROM registry.access.redhat.com/ubi8/ubi-minimal:8.6-902

RUN --mount=type=tmpfs,destination=/var/cache\
    --mount=type=cache,target=/var/cache/yum\
    --mount=type=tmpfs,destination=/root/.cache\
    --mount=type=cache,target=/root/.cache\
    microdnf update -y && microdnf install -y python3 python3-pip && python3 -m pip install --upgrade pip
WORKDIR assisted_event_scrape/

COPY requirements.txt .
RUN --mount=type=tmpfs,destination=/root/.cache\
    --mount=type=cache,target=/root/.cache\
    python3 -m pip install -I -r requirements.txt vcversioner

COPY . .
RUN --mount=type=tmpfs,destination=/root/.cache\
    python3 -m pip install .

ENTRYPOINT ["events_scrape"]
