from config import EventExportConfig, EventStoreConfig
from clients import create_es_client_from_env
from events import EventStream, EventsExporter
from storage import DateOffsetOptions, DateOffsetRepository, ObjectStorageWriter


def export_events():
    event_streams = [
        EventStream(
            EventStoreConfig.EVENTS_INDEX,
            DateOffsetOptions(
                "cluster_id",
                "event_time"
            )
        ),
        EventStream(
            EventStoreConfig.CLUSTER_EVENTS_INDEX,
            DateOffsetOptions(
                "id",
                "updated_at"
            )
        ),
        EventStream(
            EventStoreConfig.INFRA_ENVS_EVENTS_INDEX,
            DateOffsetOptions(
                "id",
                "updated_at"
            )
        ),
        EventStream(
            EventStoreConfig.COMPONENT_VERSIONS_EVENTS_INDEX,
            DateOffsetOptions(
                None,
                "timestamp"
            )
        )
    ]

    writer = ObjectStorageWriter.create_from_env()
    cfg = EventExportConfig.create_from_env()
    es_client = create_es_client_from_env()
    offset_repo = DateOffsetRepository(es_client, "offsets")

    exporter = EventsExporter(cfg, es_client, writer, offset_repo)
    for stream in event_streams:
        exporter.export_stream(stream)
