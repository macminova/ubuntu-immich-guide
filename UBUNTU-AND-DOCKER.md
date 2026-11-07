# UbuntuとDockerを準備する

[入口に戻る](START-HERE.md)。既存サーバーのアップグレード手順ではありません。

## Ubuntuのインストール

1. [Ubuntu公式](https://ubuntu.com/download/server)からUbuntu Server 26.04 LTS amd64を取得します。公式のチェックサム確認方法も参照します。
2. [公式インストール解説](https://ubuntu.com/tutorials/install-ubuntu-server)に沿ってインストールUSBを作ります。USBの中身は消えます。必要なデータを退避してください。
3. 専用PCの電源を切り、写真SSD・バックアップディスクは外します。誤消去を避けるためです。
4. USBから起動し、有線LAN、キーボード、ユーザー名・強いログインパスワードを設定します。
5. 保存先は**消してよい内蔵OSディスクだけ**を容量・型番で確認します。「ディスク全体を使用」はそのディスクを消します。既存Windowsやデータがあるなら中止します。
6. この手順は本体のキーボードと画面で進めます。SSHサーバーや追加サービスは必須ではありません。
7. インストール後USBを抜いて起動し、ログインします。

```bash
cat /etc/os-release
uname -m
free -h
df -h /
sudo apt update
sudo apt upgrade
```

26.04、x86_64、十分なRAMとOS空き容量を確認します。更新が再起動を要求した場合はここで行い、ログインし直します。手順作成者の実サーバーに接続する操作はありません。

## Dockerの導入

以下は[Docker公式Ubuntu手順](https://docs.docker.com/engine/install/ubuntu/)を基にしています。取得先はUbuntuのパッケージ配布元と `download.docker.com`。`docker --version` や `dpkg -l '*docker*'` で既存Dockerが見つかった場合は、削除せずここで止め、既存用途を先に確認します。

```bash
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl status docker --no-pager
sudo docker compose version
```

Dockerがactive、Composeが2.24.4以上なら成功です。ユーザーをdockerグループに加える操作はしません。Docker操作は管理者相当なので、内容を確認して `sudo` で実行します。

ルーターのポート開放、UPnP設定変更、ファイアウォール無効化は不要です。本手順は2283をループバックだけに束縛し、Tailscale経由で接続します。Dockerの公開ポートはUFWと独立した挙動があるため、UFWだけを信頼して全アドレス公開に変えないでください。
