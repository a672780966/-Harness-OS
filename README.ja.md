# Captain Code

> 監査可能な AI コーディングワークフロー。

![License](https://img.shields.io/badge/license-ISC-green?style=flat-square)
![Status](https://img.shields.io/badge/status-early%20development-orange?style=flat-square)
![Mode](https://img.shields.io/badge/mode-local--first-blue?style=flat-square)

[English](./README.md) · [中文](./README.zh.md) · **日本語** · [한국어](./README.ko.md)

---

## Captain Code とは

Captain Code は、開発タスクを**制御された実行・レビュー可能な証拠・ゲート判断・返却記録**へと変換する、監査可能な AI コーディングワークフローです。

開発者が AI コーディング agent を、その生の出力を盲目的に信頼することなく使えるようにします。「agent が完了したと言っている」をそのまま受け入れるのではなく、Captain Code はすべてのタスクが契約を持ち、すべての実行が証拠を残し、ゲート判断が受理するまでは何も信頼状態に入らないことを要求します。

Captain Code は**ローカルファースト（local-first）**かつ読み取り優先です。あなたのマシン上で、あなたのリポジトリに対して動作し、自ら push・公開・デプロイを行うことは決してありません。

## 解決する課題

AI コーディング agent は diff や自信に満ちた要約を生成するのは得意ですが、その作業が正しく・範囲内で・受理して安全であることを証明するのは苦手です。

- agent の主張は証拠ではありません。
- 「通った」という要約は、通ったテストではありません。
- 「完了したように見える」diff は、安全にマージできる diff と同じではありません。

agent の周りにワークフローがなければ、検証されていない出力を信頼することになります。Captain Code は agent とあなたの信頼状態の間に薄く監査可能な層を挟み、受理を「雰囲気」ではなく証拠に裏打ちされた判断にします。

## コアワークフロー

```
TaskEnvelope → Invocation → Artifact / Evidence → Review → GateDecision → AuditEvent → ReturnRecord
```

| オブジェクト   | 意味                                                            |
| -------------- | -------------------------------------------------------------- |
| `TaskEnvelope` | タスク契約：目標、範囲、受け入れ基準、制約。                    |
| `Invocation`   | 制御されたワークスペースに対する 1 回の実行試行。              |
| `Artifact`     | 生成物（diff、生成ファイル、パッチ、計画）。                    |
| `Evidence`     | 判断を支える根拠（テスト結果、ログ、ポリシーチェック）。        |
| `Review`       | artifact と evidence の評価：承認・修復・ブロック。            |
| `GateDecision` | フロー判断：`PASS` / `REPAIR` / `BLOCK` / `ESCALATE`。         |
| `AuditEvent`   | 起きたことの追記専用（append-only）記録。トレーサビリティ用。   |
| `ReturnRecord` | 状態返却記録：何が受理・拒否・未解決のまま残ったか。            |

これらは**汎用的なプロトコルオブジェクト**です。Captain Code はそのプロトコルのコーディング profile ですが、オブジェクトは再利用可能なまま保たれ、コード専用の用語に狭められることはありません。

## 最小の例

タスクは envelope として始まります：

```yaml
# task_envelope.yaml
task_id: task-001
title: "Add a usage section to README"
user_request: "Document how to run the CLI in README.md"
scope:
  allowed_paths: ["README.md"]
  denied_commands: ["git push", "git merge"]
acceptance_criteria:
  - "README has a 'Usage' section"
test_commands: ["pnpm test"]
```

そこからワークフローが実行されます：

1. **Invocation** —— worker は主チェックアウトではなく、制御されたワークスペース（git worktree）の中で実行します。
2. **Artifact / Evidence** —— diff は artifact として、ログとテスト結果は evidence として記録されます。
3. **Review** —— 受け入れ基準に照らして artifact と evidence を評価します。
4. **GateDecision** —— `PASS`、`REPAIR`、`BLOCK`、または `ESCALATE`。
5. **AuditEvent** —— すべてのステップが監査ログに追記されます。
6. **ReturnRecord** —— 何が受理され、どんなリスクが残るかの最終記録。

`GateDecision` が受理し `ReturnRecord` が書き込まれるまで、何も「完了」ではありません。

## 現在のステータス

Captain Code は**初期段階の活発な開発中**であり、その前提で扱ってください。

- **モード：** ローカルファースト・読み取り優先のセマンティック copilot。
- **現在利用可能：** プロジェクト調査、diff と証拠の収集、runner ループ（plan → execute → collect → review → gate）、レポート生成。
- **強化中：** 制御されたワークスペース実行と収束を含む、書き込み側の完全な `TaskEnvelope → ReturnRecord` ループ。
- **サンドボックスの主張ではない：** 制御されたワークスペースは git worktree です。隔離するのは*変更*であってホストではありません。セキュリティサンドボックスでは**ありません**（安全モデルを参照）。

> 命名について：CLI は現在 `harness` / `python -m harness.copilot.cli` として呼び出され、`captain-code` という名称は採用が進行中です。[docs/quickstart.md](./docs/quickstart.md) を参照してください。

## 安全モデル

Captain Code はデフォルトで保守的です。以下のルールは agent の裁量に委ねられず、ワークフローの一部として強制されます：

1. **`TaskEnvelope` がなければ、worker は実行しない。**
2. **`trace_id` がなければ、信頼された実行はない。**
3. **diff 参照がなければ、完了状態はない。**
4. **テスト結果がなければ、完了状態はない。**
5. **失敗したテストは受理にできない。**
6. **範囲外のファイル変更は隔離され**、黙って適用されることはない。
7. **コアプロトコルの変更には人間の承認が必要。**
8. **3 回連続の失敗は一時停止または人間によるレビューを引き起こす。**
9. **`git push`、公開、デプロイはブロックされる。**
10. **`ReturnRecord` が信頼される前に、受理された `GateDecision` が必要。**

制御されたワークスペースは主チェックアウトの汚染を防ぎ、変更を diff・破棄しやすくします。ただし、悪意あるコマンドがローカルファイル・環境変数・認証情報を読むことを**防ぎません**。強い隔離（コンテナ、microVM）は本段階の範囲外です。

## Captain Code が行わないこと

- 「Agent OS」や AI オペレーティングシステムでは**ありません**。
- エンタープライズガバナンスプラットフォームでは**ありません**。
- あなたの AI コーディング agent を**置き換えません** —— その出力がどう受理されるかを統治します。
- ログイン状態を**保持せず**、API キーを同梱**しません**。
- push・公開・デプロイを**行いません**。
- 自身のワークスペースがセキュアサンドボックスだと**主張しません**。

## クイックスタート

インストールと初回実行は **[docs/quickstart.md](./docs/quickstart.md)** を参照してください。

書き込み側ループの強化に伴い、完全なガイド付きクイックスタートはまだ最終調整中です。読み取り専用の調査コマンドは現在利用可能で、どのリポジトリでも安全に実行できます。

## ドキュメント

- [Quickstart](./docs/quickstart.md) —— インストールと初回実行
- [Workflow](./docs/workflow.md) —— プロトコルオブジェクトと実行ループ
- [Architecture (lite)](./docs/architecture-lite.md) —— コンポーネントと境界
- [Hermes loop lock](./docs/hermes-loop-lock.md) —— Hermes（State Machine Runner + Scheduler + Daily Reporter）の runner ルールと安全ロック

## ライセンス

ISC。
