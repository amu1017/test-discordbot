"""OpenTelemetry設定とトレース・ログ管理"""

import os
from opentelemetry.sdk.resources import Resource

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry import _logs
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk._logs.export import ConsoleLogExporter
import datetime
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    MetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

import platform
import socket
import sys
from opentelemetry.sdk.resources import ResourceDetector


def otel_providers_init() -> None:
    """OpenTelemetryの初期化とトレース・ログ設定"""

    # 環境変数から設定値を取得
    otlp_url = os.getenv("OTLP_URL", "http://localhost:4317")
    otlp_tls = os.getenv("OTLP_TLS", "false")
    service_name = os.getenv("SERVICE_NAME", "discord-bot")
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    # システムのリソース情報を付与
    resource = SystemResource().detect()

    # サービスのリソース情報の設定
    service_resource = Resource.create(
        {"service.name": service_name, "service.version": service_version}
    )
    resource = resource.merge(service_resource)

    # TracerProviderの設定
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # OTLP Span Exporterの設定（外部Collectorに送信）
    otlp_span_exporter = OTLPSpanExporter(endpoint=otlp_url, insecure=otlp_tls)
    span_processor = BatchSpanProcessor(otlp_span_exporter)
    tracer_provider.add_span_processor(span_processor)

    # LoggerProviderの設定
    logger_provider = LoggerProvider(resource=resource)
    _logs.set_logger_provider(logger_provider)

    # Console Log Exporterの設定（標準出力、1行テキスト形式）
    console_log_exporter = ConsoleLogExporter(
        formatter=lambda log_record: f"{datetime.datetime.fromtimestamp(log_record.timestamp / 1_000_000_000).strftime('%Y-%m-%d %H:%M:%S')} "
        f"- {log_record.severity_text} - {log_record.body}\n"
    )
    console_log_processor = BatchLogRecordProcessor(console_log_exporter)
    logger_provider.add_log_record_processor(console_log_processor)

    # OTLP Log Exporterの設定（外部Collectorに送信）
    otlp_log_exporter = OTLPLogExporter(endpoint=otlp_url, insecure=otlp_tls)
    log_processor = BatchLogRecordProcessor(otlp_log_exporter)
    logger_provider.add_log_record_processor(log_processor)

    # OTLP Metrics Exporterの設定（外部Collectorに送信）
    otlp_metrics_exporter = OTLPMetricExporter(endpoint=otlp_url, insecure=otlp_tls)

    # MetricReaderの設定（60秒間隔でメトリクスをエクスポート）
    metric_reader = PeriodicExportingMetricReader(
        exporter=otlp_metrics_exporter, export_interval_millis=60000  # 60秒間隔
    )

    # MeterProviderの設定
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    print(f"OpenTelemetry Provider設定終了 URL:{otlp_url}, TLS:{otlp_tls}")


class SystemResource(ResourceDetector):
    """
    platformとsocketを使い、ホストとOSの情報を検出するクラス
    """

    def detect(self) -> Resource:
        host_arch = platform.machine()
        arch_map = {"x86_64": "amd64", "aarch64": "arm64", "i386": "x86", "i686": "x86"}
        host_arch = arch_map.get(host_arch, host_arch)

        os_type = platform.system().lower()
        os_name = ""
        os_version = ""

        if os_type == "linux":
            if sys.version_info >= (3, 10):
                release_info = platform.freedesktop_os_release()
                os_name = release_info.get("NAME", "Linux")
                os_version = release_info.get("VERSION_ID", platform.release())
            else:
                os_name = "Linux"
                os_version = platform.release()
        elif os_type == "windows":
            os_name = "Windows"
            os_version = platform.version()
        elif os_type == "darwin":
            os_name = "Mac OS X"
            os_version = platform.mac_ver()[0]
        else:
            os_name = platform.system()
            os_version = platform.release()

        return Resource.create(
            {
                "host.arch": host_arch,
                "host.name": socket.gethostname(),
                "os.type": os_type,
                "os.name": os_name,
                "os.version": os_version,
            }
        )
