# CLAUDE.md

**重要**: Claude Code は常に日本語で回答すること。
**重要**: .kiro/steering も見ること

このファイルは Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

# test-discordbot

これは初期セットアップ段階にある Discord ボットプロジェクトです。

## プロジェクト構造

このプロジェクトは現在、基本的なドキュメントファイルのみのミニマルな状態です。Discord ボットを実装する際の一般的な構造は以下の通りです：

- ソースコードディレクトリ（通常は `src/` または `lib/`）
- Discord ボットトークンと設定のための設定ファイル
- コマンドハンドラーとイベントリスナー
- discord.py ライブラリ依存関係を含む requirements.txt または pyproject.toml

## 開発コマンド

このプロジェクトは discord.py を使用した Python ベースの Discord ボットです。標準的な開発コマンドは以下の通りです：

```bash
python3 -m venv venv             # venvの作成
source ./venv/bin/activate       # venvのアクティベート
pip install -r requirements.txt  # 依存関係のインストール
eval $(cat .env)                 # 環境変数の読み込み
python src/bot.py                # ボットの起動
```

## Discord ボットアーキテクチャ

discord.py を使用した Discord ボットは通常以下の構造に従います：

- discord.py クライアントまたは Bot クラスの初期化
- イベントハンドラー（on_ready、on_message、on_interaction など）
- コマンドシステム（スラッシュコマンドまたはプレフィックスコマンド）
- Cogs システムによるコマンド・イベントの整理
- 永続データのためのデータベース統合
- 環境変数によるトークンと設定の管理

## セキュリティ注意事項

- Discord ボットトークンや API キーをリポジトリにコミットしない
- 機密データには環境変数または安全な設定ファイルを使用する
- ボットコマンドに適切な権限チェックを実装する
