# 初回バックアップと復元試験

[入口に戻る](START-HERE.md)。**試験画像1枚で復元まで確認してから**大切な写真を入れます。これは手動バックアップです。自動化・遠隔保管・暗号化は今後の追加項目です。

## 別ディスクを用意する

バックアップ用ディスクは写真SSDとは物理的に別のものを使います。[SSD準備](STORAGE-SETUP.md)と同じようにデータの有無と型番を確認し、ext4を `/mnt/immich-backup` にマウントします。既存データがあれば初期化しません。fstabを使う場合も別のUUID・別のマウント先です。

```bash
findmnt --mountpoint /mnt/photos --output SOURCE,UUID,FSTYPE,TARGET
findmnt --mountpoint /mnt/immich-backup --output SOURCE,UUID,FSTYPE,TARGET
df -h /mnt/photos /mnt/immich-backup
```

別のUUID・物理ディスクであること、ext4、十分な空きを確認します。未マウントなら以下を実行しません。バックアップには写真・アカウント情報・秘密設定が含まれます。ディスクは安全に保管してください。

## 一回分を保存する

他のアップロード・更新を止めます。各行の成功を見て進み、エラー時は完成扱いしません。日時の違う保存先を作るため、既存バックアップは上書きしません。

```bash
cd /opt/immich/compose
python3 "$HOME/src/ubuntu-immich-guide/tools/immich-preflight.py"
set -o pipefail
umask 077
SNAPSHOT="/mnt/immich-backup/immich-$(date +%Y%m%d-%H%M%S)"
sudo mkdir "$SNAPSHOT"
sudo chown "$(id -un):$(id -gn)" "$SNAPSHOT"
chmod 700 "$SNAPSHOT"
sudo docker compose stop immich-server
sudo docker compose exec -T database pg_dump --clean --if-exists --username=postgres --dbname=immich | gzip > "$SNAPSHOT/database.sql.gz"
gzip -t "$SNAPSHOT/database.sql.gz"
sudo rsync -a --numeric-ids -- /mnt/photos/immich/ "$SNAPSHOT/media/"
mkdir "$SNAPSHOT/config"
cp .env docker-compose.yml docker-compose.override.yml immich-config.json "$SNAPSHOT/config/"
chmod 600 "$SNAPSHOT/config/.env"
printf '%s\n' 'v3.3.6' > "$SNAPSHOT/IMMICH-VERSION.txt"
```

`rsync --delete` は使いません。DBの生データディレクトリを稼働中にコピーする代わりにSQLダンプを保存します。上記が全て成功した場合だけ、次で内容一覧のハッシュと完了印を作ります。大量の写真ではハッシュ計算に時間がかかります。

```bash
sudo bash -o pipefail -c 'cd "$1" && find media config -type f -print0 | sort -z | xargs -0 -r sha256sum > FILES.sha256' bash "$SNAPSHOT"
(cd "$SNAPSHOT" && sha256sum database.sql.gz > DATABASE.sha256)
date -Is > "$SNAPSHOT/COMPLETE.txt"
python3 "$HOME/src/ubuntu-immich-guide/tools/immich-preflight.py" && sudo docker compose up -d immich-server
```

途中失敗なら完了印を作らず、空き容量・マウント・エラーを調べます。Immichは停止したままかもしれません。原因を直してSSD検査がPASSしてから最後の起動コマンドで戻します。既存バックアップを削除して帳尻を合わせません。

Immich標準のDB自動バックアップは写真SSD上の補助コピーです。**別ディスクへのバックアップの代用にはなりません。** この基本編では定期的に上記を手動実行する必要があります。

## 別の新品環境へ復元する

本番サーバーでは行いません。隔離した別PC・別ディスクを用意し、同じv3.3.6の手順で設定生成・起動前検査まで進め、**Immichサーバーをまだ一度も起動しない状態**にします。既存DBや写真がある復元先は対象外です。元の `.env` のUUIDやパスワードを新環境へそのままコピーしません。

1. バックアップを接続し、`COMPLETE.txt` がある回を選びます。下記の `選んだバックアップ` を実際のディレクトリ名に置き換えます。
2. ハッシュが一致しない場合は復元を中止します。写真も設定も秘密情報なので結果を公開しません。

```bash
SNAPSHOT='/mnt/immich-backup/選んだバックアップ'
sudo bash -o pipefail -c 'cd "$1" && sha256sum -c FILES.sha256' bash "$SNAPSHOT"
(cd "$SNAPSHOT" && sha256sum -c DATABASE.sha256)
gzip -t "$SNAPSHOT/database.sql.gz"
cd /opt/immich/compose
sudo rsync -a --numeric-ids -- "$SNAPSHOT/media/" /mnt/photos/immich/
sudo docker compose up -d database redis
sudo docker compose exec -T database pg_isready --username=postgres --dbname=immich
```

DBが接続受付状態になってから、[公式のCLI復元説明](https://docs.immich.app/administration/backup-and-restore/)を照合して次を実行します。これは**復元先DBを書き換える操作**です。新規・空の復元先以外には実行しません。

```bash
set -o pipefail
gzip -dc "$SNAPSHOT/database.sql.gz" | sed "s/SELECT pg_catalog.set_config('search_path', '', false);/SELECT pg_catalog.set_config('search_path', 'public, pg_catalog', true);/g" | sudo docker compose exec -T database psql --dbname=immich --username=postgres --single-transaction --set ON_ERROR_STOP=on
python3 "$HOME/src/ubuntu-immich-guide/tools/immich-preflight.py" && sudo docker compose up -d immich-server
```

SQLエラーなら停止し、既存DB削除コマンドでやり直さず原因を調べます。起動後に元ユーザーでログインし、画像・サムネイル・アルバム・ダウンロードした原本の一致を確認します。元サーバーと同時にスマートフォンの自動アップロードをつなぎません。復元成功を確認するまで元データを残します。

本手順の復元はまだ実機試験していません。成功を確認したOS・Docker・Immich版と日時を自分の非公開記録に残してください。
