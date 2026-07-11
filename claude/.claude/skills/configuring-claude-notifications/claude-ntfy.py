#!/usr/bin/env python3
"""Claude Code ntfy通知フック - JSON入力を解析して通知を送信"""

import json
import os
import socket
import sys
import time
import traceback
from pathlib import Path
from typing import Any
from urllib import request
from urllib.error import URLError


# エラーログの出力先
ERROR_LOG = Path.home() / "claude_ntfy_errors.log"

# 設定ファイルのパス
CONFIG_PATH = Path.home() / ".local/share/claude-ntfy/config.json"

# デバッグモード（環境変数または設定ファイルで制御）
DEBUG_MODE = os.environ.get("CLAUDE_NTFY_DEBUG", "false").lower() in ("true", "1", "yes")


def log_error(msg: str) -> None:
    """エラーログに出力"""
    with open(ERROR_LOG, "a") as f:
        f.write("[{}] {}\n".format(time.time(), msg))


def log_debug(msg: str) -> None:
    """デバッグログを出力（デバッグモード時のみ）"""
    if DEBUG_MODE:
        print("[DEBUG] [{}] {}".format(time.time(), msg))
        sys.stdout.flush()


def init_debug_mode() -> None:
    """設定ファイルからデバッグモードを初期化（環境変数より優先）"""
    global DEBUG_MODE
    if not CONFIG_PATH.exists():
        return
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        if isinstance(data.get("debug_mode"), bool):
            DEBUG_MODE = data["debug_mode"]
    except (json.JSONDecodeError, OSError):
        pass


class EventConfig:
    """イベントごとの通知設定"""
    def __init__(self, priority: int, title: str, tags: str):
        self.priority = priority
        self.title = title
        self.tags = tags


class HookInput:
    """Claude Codeから渡されるフック入力"""
    def __init__(self, data: dict[str, Any]):
        self.session_id = data.get("session_id", "")
        self.transcript_path = data.get("transcript_path", "")
        self.cwd = data.get("cwd", "")
        self.hook_event_name = data.get("hook_event_name", "Unknown")
        # Notification固有
        self.message = data.get("message")
        self.notification_type = data.get("notification_type")
        # Stop固有
        self.permission_mode = data.get("permission_mode")
        self.stop_hook_active = data.get("stop_hook_active")
        self.last_assistant_message = data.get("last_assistant_message")


class NtfyNotifier:
    """ntfy.shによる通知送信"""

    def __init__(self) -> None:
        self._configs: dict[str, EventConfig] = {}
        self._ntfy_url: str = ""
        self._load_config()

    def _load_config(self) -> None:
        """設定ファイルを読み込み"""
        if not CONFIG_PATH.exists():
            raise FileNotFoundError("設定ファイルが見つかりません: {}".format(CONFIG_PATH))

        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)

        self._ntfy_url = data["ntfy_url"]

        log_debug("設定ファイルを読み込み: {}".format(CONFIG_PATH))

        for event_name, config in data["events"].items():
            self._configs[event_name] = EventConfig(
                priority=config["priority"],
                title=config["title"],
                tags=config["tags"],
            )
            log_debug("イベント設定読み込み: {} (priority={}, title={}, tags={})".format(
                event_name, config["priority"], config["title"], config["tags"]
            ))

    def _get_project_name(self, cwd: str) -> str:
        """cwdからプロジェクト名を抽出"""
        if not cwd:
            return "Global"
        parts = Path(cwd).parts
        return parts[-1] if parts else "Global"

    def _sanitize_header(self, value: str) -> str:
        """HTTPヘッダー用にサニタイズ（絵文字などを削除）"""
        # ASCII文字のみを残す
        return ''.join(c for c in value if ord(c) < 128)

    def _build_message(self, hook_input: HookInput) -> str:
        """通知本文を構築"""
        project = self._get_project_name(hook_input.cwd)
        host = socket.gethostname()

        if hook_input.hook_event_name == "Notification":
            base_msg = hook_input.message or "No message"
            return "[{} @ {}] {}".format(project, host, base_msg)
        elif hook_input.hook_event_name == "Stop":
            msg = hook_input.last_assistant_message or "Task stopped"
            if len(msg) > 100:
                msg = msg[:97] + "..."
            return "[{} @ {}] {}".format(project, host, msg)
        else:
            return "[{} @ {}] Unknown event".format(project, host)

    def send(self, hook_input: HookInput) -> None:
        """通知を送信"""
        config = self._configs.get(hook_input.hook_event_name)
        if not config:
            log_error("未定義のイベント: {}".format(hook_input.hook_event_name))
            return

        body = self._build_message(hook_input)

        headers = {
            "Priority": str(config.priority),
            "Title": self._sanitize_header(config.title),
            "Tags": self._sanitize_header(config.tags),
        }

        log_debug("通知送信開始: event={}, url={}, body={}".format(
            hook_input.hook_event_name, self._ntfy_url, body
        ))
        log_debug("ヘッダー: {}".format(headers))

        req = request.Request(self._ntfy_url, data=body.encode("utf-8"), method="POST")
        for key, value in headers.items():
            req.add_header(key, value)

        try:
            with request.urlopen(req) as response:
                if response.status >= 400:
                    raise RuntimeError("HTTP {}: {}".format(response.status, response.read().decode()))
                log_debug("通知送信成功: HTTP {}".format(response.status))
        except URLError as e:
            raise RuntimeError("通知送信エラー: {}".format(e))


def main() -> None:
    """エントリーポイント"""
    try:
        init_debug_mode()
        log_debug("=== Claude ntfy通知フック開始 ===")
        # 標準入力からJSONを読み込み
        raw_input = sys.stdin.read()
        if not raw_input:
            log_error("標準入力が空です")
            sys.exit(1)

        log_debug("入力JSON: {}".format(raw_input))

        try:
            data = json.loads(raw_input)
        except json.JSONDecodeError as e:
            log_error("JSONパースエラー: {}".format(e))
            sys.exit(1)

        hook_input = HookInput(data)
        log_debug("フック入力解析: event={}, cwd={}".format(
            hook_input.hook_event_name, hook_input.cwd
        ))

        # 通知送信
        notifier = NtfyNotifier()
        notifier.send(hook_input)
        log_debug("=== Claude ntfy通知フック完了 ===")

    except Exception as e:
        log_error("通知送信失敗: {}\n{}".format(e, traceback.format_exc()))
        sys.exit(1)


if __name__ == "__main__":
    main()
