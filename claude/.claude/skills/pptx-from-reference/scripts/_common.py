"""公式 pptx スキルのパス解決とユーティリティ。"""
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("pptx-from-reference")

EMU_PER_INCH: int = 914400


def official_pptx_dir() -> Path:
    """公式 pptx スキルのルートディレクトリを返す。"""
    candidates = [
        Path.home() / ".claude" / "skills" / "pptx",
        Path("/opt/claude/skills/pptx"),
    ]
    for p in candidates:
        if (p / "SKILL.md").exists():
            return p
    raise FileNotFoundError("公式 pptx スキルが見つかりません")


def official_scripts_dir() -> Path:
    """公式 pptx スキルの scripts/ ディレクトリを返す。"""
    return official_pptx_dir() / "scripts"


def skill_root() -> Path:
    """pptx-from-reference スキルのルートディレクトリを返す。"""
    return Path(__file__).resolve().parent.parent


def emu_to_inches(emu: int) -> float:
    """EMU をインチに変換。"""
    return round(emu / EMU_PER_INCH, 3)


def inches_to_emu(inches: float) -> int:
    """インチを EMU に変換。"""
    return int(inches * EMU_PER_INCH)


def run_official_script(script_name: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    """公式 pptx スキルのスクリプトを実行。"""
    script_path = official_scripts_dir() / script_name
    if not script_path.exists():
        nested = official_scripts_dir() / "office" / script_name
        if nested.exists():
            script_path = nested
        else:
            raise FileNotFoundError(f"公式スクリプトが見つかりません: {script_name}")

    cmd = [sys.executable, str(script_path)] + args
    logger.info("Running official script: %s", " ".join(cmd))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(official_scripts_dir()),
        timeout=120,
    )
    if result.returncode != 0:
        logger.error("Script failed: %s\nstderr: %s", script_name, result.stderr)
    return result


def setup_logging(name: str = "pptx-from-reference", log_file: str | None = None) -> logging.Logger:
    """タイムスタンプ付きログ設定。"""
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    log.addHandler(sh)

    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        log.addHandler(fh)

    return log
