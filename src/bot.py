import discord
from discord.ext import commands
import os
from telemetry import setup_telemetry, get_logger, instrument, set_discord_bot
from opentelemetry import trace


# OpenTelemetryの初期化
tracer = setup_telemetry()
logger = get_logger(__name__)

# ボットの設定
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# テレメトリーシステムにボットインスタンスを設定
set_discord_bot(bot)


@bot.event
@instrument
async def on_ready():
    current_span = trace.get_current_span()
    logger.info(f"{bot.user} としてログインしました！")

    try:
        synced = await bot.tree.sync()
        logger.info(f"{len(synced)}個のグローバルスラッシュコマンドを同期しました")
    except Exception as e:
        current_span.record_exception(e)
        current_span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
        logger.error(f"コマンド同期エラー: {e}")


@bot.tree.command(name="hello", description="挨拶をします")
@instrument
async def hello(interaction: discord.Interaction):
    current_span = trace.get_current_span()

    logger.info(f"helloコマンドが実行されました - ユーザー: {interaction.user}")

    try:
        await interaction.response.send_message(
            f"こんにちは、{interaction.user.mention}さん！"
        )
        current_span.set_attribute("response.sent", True)
        logger.info(f"helloコマンドの応答を送信しました - ユーザー: {interaction.user}")
    except Exception as e:
        current_span.record_exception(e)
        current_span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
        logger.error(f"helloコマンド実行エラー: {e}")
        raise


@bot.tree.command(name="ping", description="ボットの応答時間を表示")
@instrument
async def ping(interaction: discord.Interaction):
    current_span = trace.get_current_span()
    logger.info(f"pingコマンドが実行されました - ユーザー: {interaction.user}")

    latency = round(bot.latency * 1000)
    current_span.set_attribute("bot.latency_ms", latency)
    logger.info(f"ボットのレイテンシを計測しました: {latency}ms")

    try:
        await interaction.response.send_message(f"Pong! レイテンシ: {latency}ms")
        current_span.set_attribute("response.sent", True)
        logger.info(f"pingコマンドの応答を送信しました - ユーザー: {interaction.user}")
    except Exception as e:
        current_span.record_exception(e)
        current_span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
        logger.error(f"pingコマンド実行エラー: {e}")
        raise


# ボットを起動
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        logger.info("Discordボットを起動します...")
        try:
            bot.run(TOKEN)
        except Exception as e:
            logger.error(f"ボット起動時にエラーが発生しました: {e}")
            raise
    else:
        logger.error("環境変数DISCORD_TOKENが設定されていません")
