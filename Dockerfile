FROM registry.access.redhat.com/ubi8/ubi-minimal:8.6

COPY --from=quay.io/eerez/python-builder:ubi-minimal8.6-3.6.15 /python /python-installation

RUN --mount=type=tmpfs,destination=/var/cache\
    --mount=type=cache,target=/var/cache/yum\
    --mount=type=tmpfs,destination=/root/.cache\
    --mount=type=cache,target=/root/.cache\
    microdnf update -y && microdnf install make -y && \
    cd /python-installation && make install && microdnf -y install python3-devel && rm -rf /python-installation && python3 -m pip install --upgrade pip

WORKDIR assisted_event_scrape/

COPY requirements.txt .
RUN --mount=type=tmpfs,destination=/root/.cache\
    --mount=type=cache,target=/root/.cache\
    python3 -m pip install -I -r requirements.txt vcversioner

COPY . .
RUN --mount=type=tmpfs,destination=/root/.cache\
    python3 -m pip install .

ENTRYPOINT ["events_scrape"]
