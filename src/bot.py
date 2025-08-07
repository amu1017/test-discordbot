import discord
import os
import logging
from dotenv import load_dotenv

from otel_settings import otel_providers_init
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry_instrumentation_discordpy import DiscordPyInstrumentor
from opentelemetry_instrumentation_discordpy.decorators import trace as trace_on


# 環境変数の読み込み
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

# 標準ロガーの初期化
logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)

# OpenTelemetryの初期化
otel_providers_init()

# 標準ロガーのライブラリ計装(log)
LoggingInstrumentor().instrument()

# ボットの初期化
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# Discord.pyのライブラリ計装(trace, metrics)
DiscordPyInstrumentor().instrument(client=client)


@client.event
async def on_ready():
    logger.info(f"Discord botにログインしました。{str(client.user.id)}")
    synced = await tree.sync()
    logger.info(f"スラッシュコマンドを同期しました。{len(synced)}")


@tree.command(name="hello", description="挨拶をします")
async def hello(interaction: discord.Interaction):
    response_message = f"こんにちは、{interaction.user.mention}さん"
    await interaction.response.send_message(response_message)


@tree.command(name="ping", description="ボットの応答時間を表示")
async def ping(interaction: discord.Interaction):
    latency_ms = round(client.latency * 1000)
    await interaction.response.send_message(
        msg_res(f"Pong! レイテンシ: {latency_ms}ms")
    )


@trace_on
def msg_res(text):
    return text


# ボットを起動
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        logger.info("Discordボットを起動します...")
        try:
            client.run(TOKEN)
        except Exception as e:
            logger.error(f"ボット起動時にエラーが発生しました: {e}")
            raise
    else:
        logger.error("環境変数DISCORD_TOKENが設定されていません")
