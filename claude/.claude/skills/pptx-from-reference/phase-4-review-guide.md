# Phase 4 — 自己レビュー詳細ガイド

このガイドでは、Phase 4（自己レビュー）の詳細な手順と判断基準を説明します。

---

## 4-2. 元スライドとの比較確認（必須）

各テンプレートスライドについて、以下の検証を**必ず実施**する:

### ✓ テンプレート化の完了確認（最優先）

**【重要】以下を確認してから、他の項目に進むこと:**

- [ ] **具体的なデータ（固有名詞・日付・数値・実際の文章）が残っていないか**
  - タイトル: 「テンプレートスライドN」になっているか？
  - 本文: Placeholderテキスト（【本文】...）になっているか、または削除されているか？
  - 表・グラフ: 削除されて代替矩形になっているか、または元のデータが残っていないか？
  - リード文: Placeholderテキストになっているか、または削除されているか？

#### 確認方法

**1. 元スライドと並べて画像を表示**

```python
# 元スライドとテンプレートを並べて表示
Read('_work/slide-01.jpg')  # 元スライド
Read('_work/template-1.jpg')  # テンプレート
```

**2. 目視での具体的な文言確認**

元スライドの具体的な文言を特定し、テンプレートに残っていないか確認:

- 固有名詞（例: 「日本オラクル社」「基幹システム1部開発3G」）
- 日付（例: 「10/23」「11/3週中頃」「2024年4月」）
- 具体的な進捗・タスク（例: 「CSS月例で議論実施」「品質改善方針およびドキュメント整備完了」）
- 表の内容（日付・数値・項目名）

**3. 表の内容確認**

表がある場合:
- 元スライドの表のヘッダー（列名）を確認
- 元スライドの表のデータ（日付・数値・項目）を確認
- テンプレートで表が代替矩形に置換されているか確認

#### 判断基準

- ✓ 良好: すべての具体的データがPlaceholderまたは代替矩形に置換されている
- ✗ NG: 元の文言・データが1つでも残っている → **即座に修正が必要**

**NGの例:**
- タイトルが「基幹システム1部開発3G報告」のまま（固有名詞が残存）
- 本文に「①日本オラクル社との連携品質向上」が残っている（具体的な内容が残存）
- 表に「10/23」「11/14」等の日付が残っている（実データが残存）
- リード文に「L mtg.について日本での再開が11/3週中頃」が残っている（具体的な文章が残存）

---

### ✓ コードによる検証（必須）

視覚確認だけでは不十分なため、以下のコードで全shapeのテキストを確認:

```bash
uv run python - <<'EOF'
from pptx import Presentation
prs = Presentation('template_<input>.pptx')
for slide_idx, slide in enumerate(prs.slides):
    print(f"\n=== Slide {slide_idx + 1} ===")
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text.strip():
            text = shape.text[:80].replace('\n', ' ')
            print(f"id={shape.shape_id:4d} text={text!r}")
EOF
```

#### コード出力の分析方法

**1. 出力例（良好な場合）:**

```
=== Slide 1 ===
id=   4 text='テンプレートスライド1'
id=   6 text='【表紙サブタイトル】ここにサブタイトル・部署名等を記載'
id=   5 text='【日付】YYYY年MM月DD日'

=== Slide 2 ===
id=   5 text='テンプレートスライド2'
id=   6 text='【本文】詳細説明・根拠・データなどを記載...'
```

**判断:** ✓ すべてのテキストが「テンプレートスライドN」または「【...】」形式 → 良好

**2. 出力例（NGな場合）:**

```
=== Slide 3 ===
id=  41 text='テンプレートスライド3'
id=  15 text='【リード文】要点を記載（白文字 / 強調: 黄色 / 背景: 濃紺 / 矢印記号）'
id= 123 text='①日本オラクル社との連携品質向上'
id= 124 text='・ TAM 品質管理'
id= 125 text='品質改善方針およびドキュメント整備完了後。経過観察（状況レビュー）実施した結果（予)11/14 : 改善状況確認 KDDI 内レビュー実'
```

**判断:** ✗ 元の具体的な文言（「①日本オラクル社との...」「TAM 品質管理」等）が残っている → **修正が必要**

#### 判断基準

- ✓ 良好: すべてのテキストが「テンプレートスライドN」「【...】」形式、または空
- ✗ NG: 元の具体的な文言（固有名詞、日付、詳細な説明文等）が出力される → 修正必要

**重要:** 元スライドと比較して、同じ文言が残っていないか確認すること。

---

### ✓ レイアウト・書式の保持確認

具体的なデータが削除されていることを確認した後、レイアウト・書式が保持されているか確認:

- [ ] タイトル・リード文・本文のPlaceholderが適切な位置に表示されているか
- [ ] フォント・色・サイズ・背景色が元スライドから継承されているか
- [ ] 図領域の代替長方形が適切な位置・サイズか
- [ ] Placeholderテキストがshapeからはみ出していないか（特に大フォントshape）

#### 確認方法

元スライドとテンプレートの画像を並べて比較:

**確認項目:**
1. **位置**: Placeholderが元のshapeと同じ位置にあるか
2. **フォント**: 元のフォント（ゴシック・明朝等）が保持されているか
3. **色**: 元の文字色・背景色が保持されているか
4. **サイズ**: 元のフォントサイズが保持されているか
5. **装飾**: 元の枠線・影・グラデーション等が保持されているか

**判断基準:**
- ✓ 良好: レイアウト・書式が元スライドと一致している
- ✗ NG: 位置ずれ、色の変化、フォントの変化等がある → 修正必要

---

### ✓ 不要要素の削除確認

- [ ] 削除すべきshape（具体的なデータを含む図・グラフ・表）が残っていないか
- [ ] 意図しない要素の欠落・重複がないか

#### 確認方法

**1. 削除すべきshapeの残存確認**

元スライドで削除予定だったshape（表・グラフ・具体的な図等）が残っていないか確認:

```bash
uv run python - <<'EOF'
from pptx import Presentation
prs = Presentation('template_<input>.pptx')
slide = prs.slides[N]  # 対象スライド
print(f"Total shapes: {len(slide.shapes)}")
for shape in slide.shapes:
    name = shape.name
    has_table = hasattr(shape, 'table') and shape.has_table
    has_chart = hasattr(shape, 'chart') and shape.has_chart
    print(f"id={shape.shape_id:4d} name={name:40s} table={has_table} chart={has_chart}")
EOF
```

**判断基準:**
- 表・グラフが残っている → ✗ NG（代替矩形に置換すべき）
- 削除予定の図形が残っている → ✗ NG

**2. 意図しない欠落・重複の確認**

- ロゴ・装飾が意図せず削除されていないか
- Placeholderが重複配置されていないか
- 代替矩形が重複していないか

---

## 4-3. 修正ループ

**少なくとも1回は修正→再確認サイクルを実施する**（問題ゼロに見えても必ず1周行う）。

### 修正手順

問題が見つかった場合:

1. `_work/build_template.py` を修正
2. 再実行してテンプレートを再生成
3. 4-2 の確認を繰り返す
4. 問題がなくなるまで継続

### 特に注意すべき問題と対処法

#### 1. 具体的なデータが残っている（最優先）

**問題例:**
- 本文に元の具体的な文章が残っている
- 表がそのまま残っている
- グラフのデータが残っている

**対処法:**

```python
# 本文をPlaceholder化
shape = find_shape_by_id(slide, body_id)
if shape:
    placeholder_text = '''【本文】詳細説明を記載
・文字色: #000000 / サイズ: 12pt
・強調方法: 色(#C00000) / Bold
・文体: ですます調 / 箇条書き多用
・構成: 1ペイン'''
    set_text_preserve_style(shape, placeholder_text)

# 表を削除して代替矩形に置換
table_shape = find_shape_by_id(slide, table_id)
if table_shape:
    coords = (table_shape.left, table_shape.top, table_shape.width, table_shape.height)
    remove_shape_by_id(slide, table_id)
    add_placeholder_rect(slide, *coords, '【表領域】スケジュール表を配置')
```

#### 2. Placeholderテキストがはみ出している

**問題例:**
- フォントサイズが大きい（20pt以上）shapeに長いPlaceholderテキストを設定したため、はみ出している

**対処法:**

```python
# Placeholderテキストを短縮
set_text_preserve_style(shape, '【左タイトル】')  # 短い表現にする
```

#### 3. 背景色が失われている

**問題例:**
- 元スライドで濃紺背景だったshapeが、白背景になっている

**対処法:**

```python
# shape.fill の設定を確認
# set_text_preserve_style() はテキストのみ置換するため、背景色は保持されるはず
# もし失われている場合は、shape自体を削除して再作成していないか確認
```

#### 4. 図領域の代替矩形の位置・サイズが不適切

**問題例:**
- 代替矩形が元の図と異なる位置・サイズになっている

**対処法:**

```python
# 座標の記録を再確認
shape = find_shape_by_id(slide, rm_id)
if shape:
    # 座標を正確に記録
    coords = (shape.left, shape.top, shape.width, shape.height)
    logging.info(f"Shape coords: left={coords[0]}, top={coords[1]}, w={coords[2]}, h={coords[3]}")
    remove_shape_by_id(slide, rm_id)
    add_placeholder_rect(slide, *coords, '【図領域】...')
```

---

### 最終確認

すべての修正ループが完了した後、**全スライドを改めて通しで確認する**（修正対象以外のスライドに意図しない影響が出ていないか）。

#### 最終確認時のチェックリスト

- [ ] すべてのスライドで具体的なデータが残っていないか（コード検証を実施）
- [ ] すべてのスライドでレイアウト・書式が保持されているか
- [ ] 不要なshapeが残っていないか、必要なshapeが欠落していないか

#### 最終確認の手順

1. **全スライドのコード検証を実施**

```bash
uv run python - <<'EOF'
from pptx import Presentation
prs = Presentation('template_<input>.pptx')
print("=== 全スライドのテキスト確認 ===")
for slide_idx, slide in enumerate(prs.slides):
    print(f"\n--- Slide {slide_idx + 1} ---")
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text.strip():
            text = shape.text[:60].replace('\n', ' ')
            print(f"  {text!r}")
EOF
```

出力を確認し、元の具体的な文言が残っていないか確認。

2. **全スライドの画像を通しで確認**

```bash
# 画像を順番に表示
for i in {1..5}; do
    echo "=== Slide $i ==="
    # Readツールで _work/slide-$i.jpg と _work/template-$i.jpg を確認
done
```

各スライドで:
- 具体的なデータが削除されているか
- レイアウト・書式が保持されているか
- 意図しない変更がないか

を確認。

3. **問題があれば修正ループに戻る**

---

## 修正完了の判断

以下の条件をすべて満たせば、Phase 4完了:

1. ✓ コード検証で元の具体的な文言が1つも出力されない
2. ✓ 目視確認で元の具体的なデータが残っていない
3. ✓ すべてのスライドでレイアウト・書式が保持されている
4. ✓ 不要なshapeが削除され、必要なshapeが残っている
5. ✓ 最終確認チェックリストのすべての項目がOK

**これらの条件を満たして初めて「再利用可能なテンプレート」として完成となる。**
