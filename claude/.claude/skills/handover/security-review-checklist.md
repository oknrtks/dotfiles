# 機密レビューチェックリスト（Git追跡の必須ゲート）

HANDOVER/ は Git 追跡対象。公開・共有リポジトリへの漏出リスクがあるため、引継ぎ書を**コミットする前に必ず**本チェックを実施する。レビューを通過するまでコミットしてはならない。

## 対象範囲

作成した `HANDOVER/HANDOVER-<ts>/` 配下の**全ファイル**（HANDOVER.md 本体・参考資料・logs・assets 含む）。

## 自動スキャン（grep）

まず機密パターンを機械的に検出する。対象dirで以下を実行する:

```bash
TARGET="HANDOVER/HANDOVER-<ts>"
grep -rnIE \
  -e '(api[_-]?key|secret|password|passwd|token|bearer|credential|private[_-]?key|access[_-]?key)' \
  -e 'AKIA[0-9A-Z]{16}' \
  -e 'sk-[A-Za-z0-9]{20,}' \
  -e 'gh[pousr]_[A-Za-z0-9]{36}' \
  -e 'https?://[^/@/[:space:]]+:[^/@/[:space:]]+@' \
  "$TARGET" || echo "CLEAN"
```

- ヒットした場合は**内容を確認**し、真に機密であれば伏せ字化または削除する。
- 長い base64/トークン様文字列は要精査（誤検知多めだが取りこぼし防止を優先する）。

## 目視レビューチェック項目

以下が**一切含まれていない**ことを確認する:

- [ ] APIキー・シークレット・トークン・ベアラー（z.ai, OpenAI, OCI, GitHub 等すべて）
- [ ] パスワード・パスフレーズ
- [ ] 秘密鍵（PEM 等）・SSH鍵
- [ ] 個人情報（氏名・メール・電話・住所・クレジット番号）
- [ ] 社内ホスト名・内部IP・プライベートネットワーク情報
- [ ] 認証情報入りURL（`https://user:pass@host` 形式）

## 機密の代替表現（OK例）

機密そのものを書かず、**参照**にとどめる:

- ❌ `APIキー: sk-xxxx1234`
- ✅ `APIキーは ~/.bash_local の Z_AI_API_KEY に設定済`
- ❌ `TOKEN: ghp_xxxx`
- ✅ `GitHubトークンは gh auth で設定済`

## 通過条件

- 自動スキャンで機密ヒットなし（または全て対応済み）
- 目視チェック項目すべて [x]
- → 初めてコミット可能。スキル作成フローの完了報告に「機密レビュー済」を明記する。
