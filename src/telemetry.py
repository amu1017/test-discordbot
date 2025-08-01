"""OpenTelemetry設定とトレース・ログ管理"""

import os
import logging
import datetime
from functools import wraps
import discord
from opentelemetry import trace, context
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk._logs.export import ConsoleLogExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry import _logs
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor


# グローバルなDiscordボットインスタンス
_discord_bot = None


def set_discord_bot(bot):
    """Discordボットインスタンスを設定"""
    global _discord_bot
    _discord_bot = bot


def get_discord_bot():
    """設定されたDiscordボットインスタンスを取得"""
    return _discord_bot


def setup_telemetry():
    """OpenTelemetryの初期化とトレース・ログ設定"""

    # 環境変数からCollectorエンドポイントを取得
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    # リソース情報の設定
    resource = Resource(
        attributes={
            SERVICE_NAME: "discord-bot",
            SERVICE_VERSION: "1.0.0",
            "service.instance.id": os.getenv("HOSTNAME", "local-instance"),
        }
    )

    # TracerProviderの設定
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # OTLP Span Exporterの設定（外部Collectorに送信）
    otlp_span_exporter = OTLPSpanExporter(
        endpoint=otel_endpoint, insecure=True  # 本番環境ではTLSを使用
    )
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
    otlp_log_exporter = OTLPLogExporter(
        endpoint=otel_endpoint, insecure=True  # 本番環境ではTLSを使用
    )
    log_processor = BatchLogRecordProcessor(otlp_log_exporter)
    logger_provider.add_log_record_processor(log_processor)

    # OpenTelemetryのログハンドラーを設定
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)

    # ログ設定（OpenTelemetryハンドラーのみ使用）
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s - %(message)s",
        handlers=[
            handler,  # OpenTelemetryハンドラー（Console + OTLP出力）
        ],
    )

    print(
        f"OpenTelemetryトレースとログの設定が完了しました (エンドポイント: {otel_endpoint})"
    )
    return trace.get_tracer(__name__)


def get_tracer():
    """トレーサーの取得"""
    return trace.get_tracer(__name__)


def get_logger(name):
    """OpenTelemetryログと統合されたロガーの取得"""
    return logging.getLogger(name)


def instrument(fn=None, tree="parent"):
    """OpenTelemetryトレースのためのデコレータ"""
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            # デコレータを付与する関数名・メソッド名の qualified name
            name = fn.__qualname__
            tracer = get_tracer()

            # ボット属性を設定する共通処理
            def set_bot_attributes(span):
                bot = get_discord_bot()
                if bot and hasattr(bot, "user") and bot.user:
                    span.set_attribute("bot.user", str(bot.user))
                if bot and hasattr(bot, "guilds"):
                    span.set_attribute("bot.guild_count", len(bot.guilds))

            # Discord インタラクション属性を設定する共通処理
            def set_interaction_attributes(span, interaction):
                # コマンド名を関数名から取得（qualified nameの最後の部分）
                command_name = fn.__name__
                span.set_attribute("command.name", command_name)
                span.set_attribute("user.id", str(interaction.user.id))
                span.set_attribute("user.name", str(interaction.user))
                span.set_attribute(
                    "guild.id",
                    str(interaction.guild_id) if interaction.guild_id else "DM",
                )

            # tree変数による分岐処理
            if tree == "child":
                # 子スパンとして現在のコンテキストで開始
                with tracer.start_as_current_span(name=name) as current_span:
                    set_bot_attributes(current_span)

                    # discord.Interaction が第一引数にある場合は属性を設定
                    if args and isinstance(args[0], discord.Interaction):
                        set_interaction_attributes(current_span, args[0])

                    return await fn(*args, **kwargs)
            else:
                # 親スパンとして新しいコンテキストで開始
                new_context = context.Context()
                with tracer.start_as_current_span(
                    name=name, context=new_context
                ) as current_span:
                    set_bot_attributes(current_span)

                    # discord.Interaction が第一引数にある場合は属性を設定
                    if args and isinstance(args[0], discord.Interaction):
                        set_interaction_attributes(current_span, args[0])

                    return await fn(*args, **kwargs)

        return wrapper

    # @instrument でも @instrument() でも使えるようにするため
    if fn is None:
        return decorator

    return decorator(fn)
