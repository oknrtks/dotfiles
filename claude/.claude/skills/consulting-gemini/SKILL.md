---
name: consulting-gemini
description: Consult Google Gemini API for opinions, information, or expertise when Claude lacks information, needs alternative perspectives, or requires real-time data. Use when the user explicitly asks for Gemini's opinion, when Claude doesn't have sufficient information to answer confidently, or when seeking a second AI perspective would be valuable.
---

# Consulting Gemini

Gemini AI（Google）に意見や情報を求める際に使用する。

## 実行方法

```bash
uvx git+https://github.com/oknrtks/gemini-ask "質問内容"
```

## モデル指定

ユーザーが特定のモデルを指定した場合：

```bash
uvx git+https://github.com/oknrtks/gemini-ask "質問内容" --model "gemini-2.5-pro"
```

利用可能なモデル：
- `gemini-2.5-flash`（デフォルト、高速）
- `gemini-2.5-pro`（高精度）

## 使用タイミング

このスキルは以下の場合に使用：

1. **情報不足**: Claudeが十分な情報を持っていない場合
2. **外部意見**: 第二のAI perspectiveが価値がある場合
3. **明示的な要求**: ユーザーが「Geminiに聞いて」と言った場合
4. **リアルタイム情報**: 最新の情報が必要な場合

## 出力の処理

Geminiの回答をそのままユーザーに提供する。必要に応じて要約や補足説明を追加。
