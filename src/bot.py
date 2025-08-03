import discord
import os
from discord_telemetry import setup_dc_telemetry, get_logger
from opentelemetry_instrumentation_discordpy.decorators import trace

# ボットの設定
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


# OpenTelemetryの初期化
tracer = setup_dc_telemetry(client)
logger = get_logger(__name__)


@client.event
async def on_ready():
    logger.info(f"{client.user} としてログインしました！")
    synced = await tree.sync()
    logger.info(f"{len(synced)}個のグローバルスラッシュコマンドを同期しました")


@tree.command(name="hello", description="挨拶をします")
async def hello(interaction: discord.Interaction):
    logger.info(f"helloコマンドが実行されました - ユーザー: {interaction.user}")
    response_message = f"こんにちは、{interaction.user.mention}さん"
    await interaction.response.send_message(response_message)
    logger.info(f"helloコマンドの応答を送信しました - ユーザー: {interaction.user}")


@tree.command(name="ping", description="ボットの応答時間を表示")
async def ping(interaction: discord.Interaction):
    logger.info(f"pingコマンドが実行されました - ユーザー: {interaction.user}")

    await interaction.response.send_message(
        msg_res(f"Pong! レイテンシ: {round(client.latency * 1000)}ms")
    )
    logger.info(f"pingコマンドの応答を送信しました - ユーザー: {interaction.user}")


@trace
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
