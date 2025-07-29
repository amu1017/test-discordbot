import discord
from discord.ext import commands
import os

# ボットの設定
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} としてログインしました！")
    try:
        # グローバル同期
        synced = await bot.tree.sync()
        print(f"{len(synced)}個のグローバルスラッシュコマンドを同期しました")
    except Exception as e:
        print(f"コマンド同期エラー: {e}")


@bot.tree.command(name="hello", description="挨拶をします")
async def hello(interaction: discord.Interaction):
    print(f"helloコマンドが実行されました - ユーザー: {interaction.user}")
    await interaction.response.send_message(
        f"こんにちは、{interaction.user.mention}さん！"
    )


@bot.tree.command(name="ping", description="ボットの応答時間を表示")
async def ping(interaction: discord.Interaction):
    print(f"pingコマンドが実行されました - ユーザー: {interaction.user}")
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! レイテンシ: {latency}ms")


# デバッグ用: すべてのインタラクションをログ
@bot.event
async def on_interaction(interaction: discord.Interaction):
    print(f"インタラクション検出: {interaction.type} - {interaction.data}")
    if interaction.type == discord.InteractionType.application_command:
        print(f"アプリケーションコマンド: {interaction.data.get('name', 'unknown')}")


# ボットを起動
if __name__ == "__main__":
    # 環境変数からトークンを取得
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("DISCORD_TOKENが設定されていません！")
