# はじめて構築する方へ

対象は**新しい専用PCに入れるUbuntu Server 26.04 LTS amd64**です。既存サーバーへの上書き手順ではありません。CPU 2コア以上、RAM 8GB以上を目安に、OS・DB用の内蔵SSD、写真用ext4 SSD、別のバックアップ用ディスクを用意します。Windows PCを消してUbuntuにする必要はありません。専用PCがない場合はここで止めてください。

これは2026-11-08作成の**実機検証前の手順案**です。Immich v3.3.6に固定しています。古くなった場合はセキュリティ情報と対応版を確認し、版番号だけを置き換えないでください。大切な写真を最初の試験に使いません。

## 進める順番

1. [UbuntuとDocker](UBUNTU-AND-DOCKER.md)を入れる。
2. [写真SSD](STORAGE-SETUP.md)を準備する。
3. 以下でImmichを準備する。
4. [Tailscaleとスマートフォン](TAILSCALE-AND-PHONE.md)を接続する。
5. [バックアップと復元](BACKUP-HOWTO.md)を試す。

基本編では画像認識・顔認識・意味検索用の機械学習サービスを起動しません。中国企業由来モデルを未確認のまま取得しないためです。写真の保存・閲覧は先に試します。顔認識等が必要な方は別途モデルの由来を確認してください。

## 1. ガイドを取得する

以下はUbuntuの端末で、一つずつ実行します。エラーが出たら先へ進まず、[トラブル対処](TROUBLESHOOTING.md)を確認してください。

```bash
sudo apt update
sudo apt install git python3 curl rsync
mkdir -p "$HOME/src"
git clone https://github.com/macminova/ubuntu-immich-guide.git "$HOME/src/ubuntu-immich-guide"
cd "$HOME/src/ubuntu-immich-guide"
test -f tools/immich-preflight.py
```

最後が失敗する場合、GitHubに今回の新しい手順がまだ反映されていません。古い公開版のまま続けないでください。取得時点のコミットは `git rev-parse HEAD` で控えます。

## 2. 新規の作業場所を作る

`/opt/immich/compose` が既にある場合は止めます。既存環境の移行は対象外です。

```bash
sudo mkdir -p /opt/immich
sudo mkdir /opt/immich/compose
sudo chown "$(id -un):$(id -gn)" /opt/immich/compose
chmod 700 /opt/immich/compose
cd /opt/immich/compose
curl --fail --location --output docker-compose.yml https://github.com/immich-app/immich/releases/download/v3.3.6/docker-compose.yml
cp "$HOME/src/ubuntu-immich-guide/examples/docker-compose.override.yml" .
cp "$HOME/src/ubuntu-immich-guide/examples/immich-config.json" .
```

取得元はImmich公式GitHubです。コンテナ取得時にはGHCR・Docker Hubへの通信も発生します。アカウントの秘密情報は貼り付けません。

## 3. SSD確認と秘密設定の生成

[SSD準備](STORAGE-SETUP.md)で確認した写真ディスクのUUIDを使います。`実際の写真SSDのUUID` は文字通り貼らず、自分の値に置き換えてください。これはパスワードではありませんが公開する必要はありません。

```bash
cd /opt/immich/compose
python3 "$HOME/src/ubuntu-immich-guide/tools/immich-preflight.py" --init --ssd-uuid '実際の写真SSDのUUID'
```

成功すると `.env` が権限600で作られ、PASSが表示されます。DBパスワードはランダム生成され、表示されません。既存の `.env` は上書きしません。ファイルをGitHubへアップロードしないでください。

## 4. 起動前検査

Docker Compose **2.24.4以上**が必要です。`!override` を解釈できない版は使用しません。

```bash
sudo docker compose version
python3 "$HOME/src/ubuntu-immich-guide/tools/immich-preflight.py"
set -o pipefail
sudo docker compose config --format json | python3 "$HOME/src/ubuntu-immich-guide/tools/verify-compose.py"
```

両方PASSになってから起動します。`docker compose config` の出力にはパスワードが含まれるので、パイプを外して公開したりログに保存したりしません。検査ツールは全脅威を検出する監査器ではなく、本ガイドの保存先・公開ポート等の事故防止用です。

```bash
sudo docker compose pull immich-server redis database
sudo docker compose up -d immich-server redis database
sudo docker compose ps
curl --fail http://127.0.0.1:2283/api/server/ping
sudo ss -ltnp 'sport = :2283'
```

初回取得には時間がかかります。pingで応答し、待受が `127.0.0.1:2283` のみなら次へ進みます。`0.0.0.0`・`[::]` の2283待受があれば停止し、接続設定を見直します。DB・Redisのポートを外へ公開しません。

## 再起動後の起動方法

この基本編は**自動起動しません**。SSDが外れた状態での起動を防ぐため、再起動後もSSD確認をしてから手動で起動します。常時稼働向けのマウント連動自動起動は今後の追加項目です。

```bash
cd /opt/immich/compose
python3 "$HOME/src/ubuntu-immich-guide/tools/immich-preflight.py" && sudo docker compose up -d immich-server redis database
```

起動中にSSDを抜くことは防げません。取り外す前にはこのディレクトリで `sudo docker compose stop` を実行し、停止を確認します。最初は試験画像1枚で進め、バックアップの復元確認後に本格利用してください。
