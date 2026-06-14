
<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0--rc.2-blue?style=flat-square" alt="バージョン">
  <img src="https://img.shields.io/badge/TypeScript-6.0-blue?style=flat-square" alt="TypeScript">
  <img src="https://img.shields.io/badge/license-ISC-green?style=flat-square" alt="ライセンス">
  <img src="https://img.shields.io/badge/tests-528%20passed-brightgreen?style=flat-square" alt="テスト">
</p>

<p align="center">
  <a href="README.md"><strong>🇬🇧 English</strong></a> ·
  <a href="README.zh.md"><strong>🇨🇳 中文</strong></a> ·
  <a href="README.ja.md"><strong>🇯🇵 日本語</strong></a> ·
  <a href="README.ko.md"><strong>🇰🇷 한국어</strong></a>
</p>

<h1 align="center">Harness OS</h1>
<p align="center"><em>Codex‑first プロジェクトオペレーティングシステム — ガバナンス、監査、再現可能なエージェントエンジニアリング</em></p>

---

**Harness OS** は AI コーディングエージェントのためのオペレーティングシステムです。フレームワークがエージェントに*能力*を与えるのに対し、Harness OS は*境界と規律*を与えます。すべてのツール呼び出しはゲートを通り、すべての出力はマスクされ、すべての意思決定は追跡され、すべてのデリバリーは検証されます。

これは **AI エージェントのための Kubernetes** と考えてください — コンテナを実行するためではなく、ガバナンス、可観測性、監査性を備えたエージェンティックワークフローを実行するためのものです。

---

## なぜ Harness OS なのか？

LangChain、Vercel AI SDK、OpenAI Agents SDK といったフレームワークは、エージェントにツール呼び出しやモデル利用、ワークフロー構成の能力を与えます。しかし、それらは以下の問いに答えられません：

- **誰がこのツール呼び出しを承認したのか？** → Harness OS はセッション、ターン、エージェント ID ですべての呼び出しを追跡します。
- **出力に機密情報が漏れていないか？** → Harness OS は 15 以上の機密パターンをすべての出力境界で自動マスクします。
- **何が起こったかを再生できるか？** → すべての実行はイベント、承認、チェックポイントを含む構造化トレースとして記録されます。
- **デリバリーは安全か？** → commit、PR、deploy の前に、暗号学的完全性ハッシュによる検証が必須です。
- **ポリシーを強制できるか？** → 不変フィールド、単方向セーフティルール、fail‑closed デフォルトを備えた多層構成。

Harness OS は**フレームワークではありません**。あらゆるエージェントランタイムをラップして本番環境に対応させる**ガバナンスレイヤー**です。

---

## アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│                   CLI (harness)                      │
│  create │ open │ init │ run │ verify │ deliver        │
│  config │ status │ report │ checkpoint │ rollback     │
│  skills │ decision │ repair │ check                   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                 Turn Orchestrator                     │
│  Session → Input → Model Call → Tool Gate → Response │
└──────┬─────────┬──────────┬──────────┬─────────────┘
       │         │          │          │
┌──────▼──┐ ┌───▼────┐ ┌──▼────┐ ┌──▼──────────┐
│ Policy  │ │Approval│ │Secret │ │Observability │
│ Engine  │ │ Gate   │ │Redact │ │ Trace/Events │
└─────────┘ └────────┘ └───────┘ └──────────────┘
       │         │          │          │
┌──────▼─────────▼──────────▼──────────▼──────────┐
│            Verification & Delivery                │
│  Guard → Commit → PR → Release → Deploy          │
└──────────────────────────────────────────────────┘
```

### Thin Harness（実装済み）

すべてのエージェントアクションをガバナンスする最小実行可能ループ：

1. ターン入力を受信
2. モデル呼び出しを実行
3. ツール提案を生成
4. **PreToolUse ゲート** — ポリシー評価 + 機密スキャン
5. **Allow / Deny / NeedsApproval** 判定
6. **承認解決**（必要な場合）
7. ツール実行
8. **PostToolUse トレース** — すべてを記録
9. マスク処理された最終応答

### Thick Harness（計画中）

プロダクション規模のデプロイのための拡張機能：
- 並列フックファンアウト（パブリッシュ＆コレクト）
- OpenTelemetry 統合
- 再起動不要のポリシーホットリロード
- マルチプロバイダーフェイルオーバー（Claude ↔ GPT ↔ 他）
- 予算ベースのプロバイダールーティング
- 分散承認 UI
- サンドボックス化されたツール実行

---

## クイックスタート

### 前提条件

- [Node.js](https://nodejs.org/) >= 22
- [pnpm](https://pnpm.io/) >= 11

### インストールとビルド

```bash
git clone https://github.com/a672780966/-Harness-OS.git
cd Harness-OS
pnpm install
pnpm build
```

### 実行

```bash
# バージョン表示
pnpm harness --version
# → 1.0.0-rc.2

# ヘルプ表示
pnpm harness --help

# 設定表示
pnpm harness config

# 設定表示（JSON）
pnpm harness config --json

# スキル一覧
pnpm harness skills list

# AGENTS.md の妥当性確認
pnpm harness check

# プロジェクトで Harness OS を初期化
pnpm harness init --json

# タスクを実行
pnpm harness run "認証モジュールのテストを追加"
```

### 一般的なワークフロー

```bash
# 1. プロジェクトを初期化
cd my-project
harness init

# 2. タスクを実行
harness run "ユーザー認証を実装"

# 3. 検証を実行
harness verify

# 4. デリバリーを準備
harness deliver --commit --ver-id <検証ID>
```

---

## CLI コマンド

| コマンド | 説明 |
|---|---|
| `create <name>` | 新しい Harness OS プロジェクトを作成 |
| `open <path>` | 既存のプロジェクトを開く |
| `init` | 既存プロジェクトで Harness OS を初期化 |
| `repair` | 欠落または無効なプロジェクト構造を修復 |
| `check` | AGENTS.md の妥当性を確認 |
| `status` | 現在のプロジェクト状態を表示 |
| `run <task>` | タスクを実行（完全パイプライン） |
| `resume <run-id>` | 一時停止または中断された実行を再開 |
| `verify` | 検証パイプラインを実行（lint、型検査、テスト、ビルド） |
| `report <run-id>` | 実行レポートを表示 |
| `deliver` | デリバリーを準備（commit / PR / release / deploy） |
| `decision` | アーキテクチャ決定を管理（ADR） |
| `skills` | スキルを管理・一覧表示 |
| `checkpoint` | git とタスク状態を保存するチェックポイントを作成 |
| `rollback <checkpoint-id>` | ロールバック情報を表示 |
| `config` | Harness OS 設定を表示 |

すべてのコマンドは `--json`（機械可読出力）と `--quiet`（最小出力）をサポートしています。

---

## 内蔵機能

### ガバナンスとセキュリティ
- **権限三状態**: `allow` | `deny` | `needs_approval` — 曖昧な状態なし
- **機密マスキング**: 15 以上のパターン — API キー、トークン、秘密鍵をすべての出力から自動マスク
- **ファイル保護**: 危険なパスへのエージェントアクセスをブロック
- **セーフティフィールド**: 不変設定フィールド、単方向弱体化防止、ユニオンマージ配列
- **Fail‑closed**: フック障害はデフォルトで `needs_approval`

### 検証
- `AGENTS.md` と `package.json` からプロジェクトコマンドを自動検出
- 完全パイプラインを実行：lint → 型検査 → テスト → ビルド
- 暗号学的完全性ハッシュ付き構造化 JSON 結果を生成
- プロジェクト、タスク、実行、git commit にバインドされ、否認防止を実現

### デリバリーパイプライン
- ガードチェック：検証バインディング、git 状態、プロジェクト整合性
- 規約ベースのコミットメッセージ生成
- PR 本文生成
- 完全な監査証跡付きデリバリーレポート

### 可観測性
- **イベント**: セッション、アクター、マスキング付き JSONL イベントログ
- **トレース**: ツール呼び出し、コンテキストパック、チェックポイントを含む完全な実行トレース
- **レポート**: 検証結果付き Markdown 実行レポート

### スキルレジストリ
リスク分類と承認要件に基づく内蔵スキル：

| スキル | リスク | ツール |
|---|---|---|
| Filesystem | 中 | 読み取り、書き込み、一覧、検索、削除 |
| Shell | 高 | コマンド実行、テスト、ビルド |
| Git | 中 | 状態、差分、コミット、プッシュ |
| Repo Scanner | 低 | スキャン、検出、マッピング |

---

## プロジェクト構造

```
Harness-OS/
├── src/
│   ├── cli/              # CLI エントリポイント + フォーマッター
│   ├── config/           # 階層型設定ローダー（セーフティ対応）
│   ├── governance/       # ポリシーエンジン、マスカー、フックフレームワーク
│   ├── project/          # プロジェクトライフサイクル（作成/開く/初期化/修復）
│   ├── task/             # タスクライフサイクル（作成/完了/失敗）
│   ├── decision/         # ADR 管理（提案/承認/却下）
│   ├── verification/     # 検証パイプライン + 結果バインディング
│   ├── delivery/         # デリバリーパイプライン（ガード/コミット/PR/レポート）
│   ├── observability/    # イベント、トレース、実行レポート
│   ├── runtime/          # セッション、パイプライン、ターンオーケストレーター
│   ├── context/          # コンテキストパック構築
│   ├── skills/           # MCP スキルレジストリ
│   └── state/            # 実行、チェックポイント、SQLite 状態
├── tests/
│   ├── unit/             # 528 単体テスト
│   └── integration/      # 28 統合テスト
├── harness_os_docs/      # 完全な設計仕様（12 ドキュメント）
├── .claude/              # Claude Code プロジェクト設定
└── .project/             # Harness OS ローカル状態（gitignore）
```

---

## ドキュメント

完全な設計・エンジニアリング仕様は [`harness_os_docs/`](harness_os_docs/README.md) にあります：

| ドキュメント | 説明 |
|---|---|
| [01_ARCHITECTURE](harness_os_docs/01_ARCHITECTURE.md) | システムアーキテクチャとコア原則 |
| [02_CODEX_DEVELOPMENT_SPEC](harness_os_docs/02_CODEX_DEVELOPMENT_SPEC.md) | Codex 開発仕様 |
| [03_AGENTS_MD_STANDARD](harness_os_docs/03_AGENTS_MD_STANDARD.md) | AGENTS.md プロトコル標準 |
| [04_HARNESS_OS_DESIGN](harness_os_docs/04_HARNESS_OS_DESIGN.md) | 詳細システム設計 |
| [05_CONTEXT_ENGINEERING](harness_os_docs/05_CONTEXT_ENGINEERING.md) | コンテキストエンジニアリング仕様 |
| [06_TASK_DECISION_PROJECT_MANAGER](harness_os_docs/06_TASK_DECISION_PROJECT_MANAGER.md) | タスク、決定、プロジェクト管理 |
| [07_MCP_SKILLS_SPEC](harness_os_docs/07_MCP_SKILLS_SPEC.md) | MCP スキル仕様 |
| [08_GOVERNANCE_SECURITY](harness_os_docs/08_GOVERNANCE_SECURITY.md) | ガバナンスとセキュリティルール |
| [09_VERIFICATION_OBSERVABILITY](harness_os_docs/09_VERIFICATION_OBSERVABILITY.md) | 検証と可観測性 |
| [10_DELIVERY_PIPELINE](harness_os_docs/10_DELIVERY_PIPELINE.md) | デリバリーパイプライン仕様 |
| [11_ACCEPTANCE_CRITERIA](harness_os_docs/11_ACCEPTANCE_CRITERIA.md) | 最終合格基準 |
| [12_OPEN_SOURCE_REFERENCES](harness_os_docs/12_OPEN_SOURCE_REFERENCES.md) | オープンソース参照マッピング |
| [13_TESTING_STRATEGY](harness_os_docs/13_TESTING_STRATEGY.md) | テスト戦略 |
| [14_ERROR_CODES](harness_os_docs/14_ERROR_CODES.md) | エラーコードリファレンス |
| [15_CONFIG_REFERENCE](harness_os_docs/15_CONFIG_REFERENCE.md) | 設定リファレンス |
| [16_CLI_OUTPUT_CONTRACT](harness_os_docs/16_CLI_OUTPUT_CONTRACT.md) | CLI 出力契約 |
| [17_PROJECT_STORAGE_GIT_POLICY](harness_os_docs/17_PROJECT_STORAGE_GIT_POLICY.md) | Git とストレージポリシー |
| [18_MIGRATION_VERSIONING](harness_os_docs/18_MIGRATION_VERSIONING.md) | 移行とバージョニング |

---

## 開発

```bash
# 型検査
pnpm typecheck

# 単体テスト実行
pnpm test:unit

# 統合テスト実行
pnpm test:integration

# 全テスト実行
pnpm test

# カバレッジ付きテスト実行
pnpm test:coverage

# ビルド
pnpm build

# コードフォーマット
pnpm format
```

### テスト状況

- **528 単体テスト** — 19 テストファイル、すべて成功
- **28 統合テスト** — 1 テストファイル、すべて成功
- **カバレッジ閾値**: 80%（vitest.config.ts で設定）
- **TypeScript**: 厳格モード、`src/` から `as any` を完全排除

---

## 設計原則

1. **境界の明確さ**: 各モジュールに明確な責務。神オブジェクトなし。
2. **保守的な権限**: デフォルトは `needs_approval`。決して `allow` をデフォルトにしない。
3. **状態の追跡可能性**: すべての書き込みにスキーマ、スコープ、アクター、理由、トレース ID がある。
4. **ツール呼び出しの監査可能性**: すべての呼び出しが誰が、何を、入力を、判断を、タイムスタンプを記録する。
5. **低結合**: Thin Harness 優先。Thick Harness は拡張として決して混在させない。
6. **Fail‑closed**: フックの失敗、タイムアウト、解析不能な結果 → `needs_approval`。

---

## ステータス

**v1.0.0-rc.2** — コアガバナンスと検証のリリース候補。

実装済み：
- ✅ CLI フレームワーク（17 コマンド）
- ✅ 多層設定 + セーフティフィールド強制
- ✅ 機密マスキング（15+ パターン、全出力境界をカバー）
- ✅ 整合性バインディング付き検証パイプライン
- ✅ ガードチェック付きデリバリーパイプライン
- ✅ 可観測性（イベント、トレース、実行レポート）
- ✅ ADR 管理（提案/承認/却下/置き換え）
- ✅ セッションと状態管理
- ✅ タスクライフサイクル（作成 → 実行 → 完了 → レポート）
- ✅ スキルレジストリ（4 つの内蔵スキル）
- ✅ チェックポイントとロールバック分析
- ✅ 528 単体テスト + 28 統合テスト

v1.1+ 計画：
- ポリシーホットリロード
- マルチプロバイダーランタイム（Claude + GPT + オープンモデル）
- 分散承認 UI
- OpenTelemetry エクスポート
- サンドボックス化されたツール実行

---

## ライセンス

ISC
