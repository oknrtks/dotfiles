#!/bin/bash

# dotfilesディレクトリの場所（スクリプトの場所を基準にする）
DOT_DIR=$(cd $(dirname $0); pwd)
cd $DOT_DIR

# 管理したいパッケージ（ディレクトリ名）のリスト
PACKAGES=("bash" "tmux" "claude")

echo "Starting dotfiles setup..."

for pkg in "${PACKAGES[@]}"; do
    echo "Installing package: $pkg"

    # stow -n (dry-run) で衝突するファイルを確認し、あればリネーム
    # --dotfiles オプションを使うと 'dot-bashrc' を '.bashrc' として展開も可能ですが
    # 今回はシンプルな標準構成で進めます
    
    stow -Rnv $pkg 2>&1 | grep "existing target is not an owned link" | awk '{print $NF}' | while read -r file; do
        # 重複する実体ファイルがある場合のみバックアップ
        if [ -e "$HOME/$file" ] && [ ! -L "$HOME/$file" ]; then
            echo "Backing up: $HOME/$file to $HOME/$file.old"
            mv "$HOME/$file" "$HOME/$file.old"
        fi
    done

    # 実際にリンクを貼る (-R は再実行・更新)
    stow -R $pkg
done

echo "Setup completed!"