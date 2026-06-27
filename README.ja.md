
<p align="center">
  <img src="https://img.shields.io/badge/version-v1.4--loop--installer--mvp-blue?style=flat-square" alt="バージョン">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/copilot_tests-616%20passed-brightgreen?style=flat-square" alt="Copilot テスト">
  <img src="https://img.shields.io/badge/full_pytest-848%20passed-brightgreen?style=flat-square" alt="全テスト">
  <img src="https://img.shields.io/badge/license-ISC-green?style=flat-square" alt="ライセンス">
</p>

<p align="center">
  <a href="README.md"><strong>🇬🇧 English</strong></a> ·
  <a href="README.zh.md"><strong>🇨🇳 中文</strong></a> ·
  <a href="README.ja.md"><strong>🇯🇵 日本語</strong></a> ·
  <a href="README.ko.md"><strong>🇰🇷 한국어</strong></a>
</p>

<p align="center">
  <img src="assets/brand/mobius-homepage-hero-v1.png" width="360" alt="Mobius — AI 生産プロセスのための時間ガバナンスシステム">
</p>
<h1 align="center">Mobius</h1>
<p align="center"><em>AI 生産プロセスのための時間ガバナンスシステム</em></p>

---

**Mobius は、生成系システムのための時間治理構造です。**

目的が行動を制約し、
証拠が信頼を支え、
記憶が結果を保存し、
境界が能力を形成し、
進化が未来の判断を修正します。

永続的なエージェントを作るのではありません。
一時的な実行を、証拠、記憶、境界、能力、あるいは明確な判断としてシステムに還元します。

<p align="center">
  <a href="#クイックスタート"><strong>▶ 5分で始める</strong></a>
</p>

---

## Mobius の存在理由

現代の AI エージェントは、推論、コーディング、ツール使用、マルチエージェント連携において急速に能力を高めています。しかし、能力だけでは AI 生産プロセスを信頼できるものにできません。

より難しい問題はガバナンスです：

- 目標は誰が定義するのか？
- タスクは誰が実行するのか？
- ツールアクセスは誰が許可するのか？
- 結果は誰が評価するのか？
- 継続、停止、再試行、ロールバック、人間への引き継ぎは誰が判断するのか？

現在のエージェントフレームワークは「どのように実行するか」に答えます。Mobius は「時間を超えて実行をどう治理するか」に答えます。

**Mobius が存在する理由は、AI 生産には強力なエージェントだけでなく、すべての行動が証拠、記憶、境界、またはより良い判断として還元されることを保証する時間指向の治理構造が必要だからです。**

---

## クイックスタート

```bash
git clone https://github.com/a672780966/-Harness-OS.git
cd -Harness-OS
# オプション 1: Python CLI（インストール不要）
python -m harness.copilot.cli version --json
python -m harness.copilot.cli doctor
python -m harness.copilot.cli inspect .
python -m harness.copilot.cli dashboard .
python -m harness.copilot.cli pr-draft --base main

# オプション 2: Node CLI（pnpm + node が必要）
pnpm install
pnpm build
./dist/index.js version --json
./dist/index.js doctor
```

`harness` コマンドが利用できない場合：
```bash
python -m harness.copilot.cli version --json
python -m harness.copilot.cli doctor
```
ビルド後（`pnpm install && pnpm build`）、`harness` バイナリは `./dist/index.js` にあります。

---

## コア哲学

### 目的は行動に先立つ (Purpose Before Action)

すべての実行は明確な目的に奉仕しなければなりません。エージェントは行動する前に、なぜ始めるのか、どこへ向かうのか、何をもって完了とするのか、何を裏切ってはならないのかを知る必要があります。

### すべての行動は還元されなければならない (Every Action Must Return)

実行は常に結果を生みます。結果は一時的なエージェントとともに消えてはなりません。証拠、軌跡、リスク、コスト、失敗、境界、能力としてシステムに還元されなければなりません。

### 証拠は信頼に先立つ (Evidence Before Trust)

AI は完了を自己証明できません。エージェントの主張は証拠ではありません。信頼は trace、diff、test、review、audit、および高リスクまたは最終権限シナリオにおける人間の承認から生まれます。

### 能力は境界から生まれる (Capability Emerges from Boundaries)

真の能力とは「何でもできる」ことではありません。いつ行動すべきか、どこで止めるべきか、何に証拠が必要か、何を人間に委ねるべきかを知ることです。

### システムは進化しなければならない (The System Must Evolve)

エージェントは一時的で構いません。ワーカーは破棄できます。タスクは終了できます。しかしシステムは立ち止まってはいけません。すべての行動の後、Mobius は判断します：これを記憶として堆積すべきか？能力を生成すべきか？境界を更新すべきか？判断を人間に戻すべきか？

---

## アーキテクチャ

Mobius は AI 生産プロセスを 4 つの時間治理層に分割します。

### Future Layer（目標制約）
未来は予測ではなく制約です。目的、目標、合格基準、プロジェクト方向、不可違反の不変条件を保存します。

### Present Layer（一時実行）
現在は一時的なエージェントが限られた権限内で検証可能なタスクを実行する場です。タスク実行、ツール呼び出し、コード変更、テスト実行、証拠生成を担当します。

### Past Layer（経験堆積）
過去はチャットログではありません。証拠によって検証されたシステム記憶です。実行軌跡、失敗原因、修正経路、テスト結果、監査イベント、決定記録を保存します。

### Evolution Layer（システム進化）
特定の実行には参加せず、システム全体が改善されているかを判断する唯一の層です。

---

## Harness OS：参照実装

Harness OS は、Mobius Architecture の最初で現在唯一の参照実装です。

Captain、Worker、Audit、StarMap、Loop Controller、Tool Gateway を含むランタイム層を、Mobius の原則をコードで enforce する具体的なエンジニアリング製品として実装しています。

- **理論上の代替可能性**：Mobius Architecture は特定のランタイムに依存しません。他の実装も可能です。
- **実際上の唯一性**：Harness OS は最初で現在唯一の参照実装です。

Harness OS はモデルプロバイダーでも、汎用コーディングフレームワークでも、クラウド SaaS 製品でもありません。AI 支援エンジニアリングのためのローカルファーストなガバナンスランタイムです。

---

## 現在のステータス

- **ベースライン**: `v1.4-loop-installer-mvp`
- **Copilot テスト**: `616 passed`
- **全テスト**: `848 passed`
- **モード**: local-first semantic copilot

### v1.1 — Real Hermes Loop
グラフプランナー、ループランナー/コントローラー、実行/監査、評価トリガー修正、レビュートリガー修正、ファイナルゲート、証拠パック

### v1.2 — Local Semantic Copilot MVP
プロジェクト検査、差分サマリー、タスクカード、マージ準備状態、証拠パック、静的シェル、リアルタイムモニター、エージェント状態機械、PR/MR パック、プロバイダー信頼性ガード、ライブダッシュボード

### v1.3 — ランタイム基盤
設定スキーマ/ローダー/リゾルバー/バリデーター、ランダイムドクター、バージョンコマンド、プロバイダー信頼性計画

### v1.3.1 — PR ドラフトアシスタント
`harness copilot pr-draft`、GitHub CLI 検出、手動フォールバック PR ドラフト生成、大ファイル/キャッシュブロックチェック

---

## タグ / 証拠ポリシー

一部のローカル sealed タグは、到達可能な履歴に 373 MB の SWE-bench 証拠アーカイブが含まれているため、GitHub にプッシュされていません。公開安全タグのみがプッシュされます。

---

## 重要ドキュメント

- [v1.3 Main Integration Seal](docs/v1_3_main_integration_seal.md)
- [v1.2 Alpha Final Seal Manifest](docs/v1_2_alpha_final_seal_manifest.md)
- [Public-Safe Evidence Strategy](docs/public_safe_evidence_strategy.md)
