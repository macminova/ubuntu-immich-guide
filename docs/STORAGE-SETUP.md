# 写真SSDを準備する

[入口に戻る](START-HERE.md)。写真SSDは `/mnt/photos`、DBは内蔵SSDの `/srv/immich-db/postgres` に分けます。写真SSDのコピーだけではDBを復元できません。

## 1. ディスクを特定する

Ubuntuを停止して写真SSDだけを接続し、起動します。バックアップディスクはまだ接続しません。

```bash
lsblk -o NAME,MODEL,SIZE,FSTYPE,UUID,MOUNTPOINTS
```

型番・容量で写真SSDを特定します。`/dev/sdb` 等の名前は接続順で変わるので固定しません。既存写真や必要なデータがある、OSディスクと区別できない場合は**ここで停止**します。

この手順はext4の単一データパーティションを前提にします。NTFS/exFATをそのまま使う手順ではありません。変換・初期化すれば元データが消える場合があります。

### 新品・空ディスクをext4にする場合だけ

初期化は破壊的な別工程です。必要データがないことを確認し、OSディスク以外を識別できる場合だけ行います。Ubuntu DesktopのLive USBを「試す」で起動し、「ディスク」アプリで**型番と容量が一致する写真SSD**を選択し、パーティション作成・ext4でのフォーマットを行います。ダイアログの対象を再確認します。判断できなければ初期化せず相談してください。OSをインストールする必要はありません。完了後Ubuntu Serverへ戻ります。

## 2. UUIDでマウントする

`lsblk` で写真用ext4パーティションのUUIDを控えます。以下の `写真SSDのUUID` を実際の値に置き換えます。

```bash
sudo mkdir -p /mnt/photos
sudo cp --no-clobber /etc/fstab /etc/fstab.before-immich
sudoedit /etc/fstab
```

既存行を削除せず、次の1行を追加します。同じUUID・同じマウント先が既にある場合は重複追加しません。

```text
UUID=写真SSDのUUID /mnt/photos ext4 defaults,nofail,nodev,nosuid 0 2
```

```bash
sudo systemctl daemon-reload
sudo mount /mnt/photos
findmnt --mountpoint /mnt/photos --output SOURCE,UUID,FSTYPE,TARGET
```

UUIDが控えた値、FSTYPEがext4、TARGETが `/mnt/photos` と一致する場合だけ次へ進みます。何も出ない場合や別ディスクなら止めます。`nofail` はSSDなしでもOSを起動させる設定で、Immichの安全な起動を保証するものではありません。

## 3. 保存ディレクトリを作る

マウント確認が済んでから実行します。既存の `immich` やDBディレクトリがあれば、新規構築として扱わず止めてください。

```bash
sudo mkdir /mnt/photos/immich
sudo mkdir -p /srv/immich-db
sudo mkdir /srv/immich-db/postgres
df -h /mnt/photos /srv/immich-db
```

全体を `chmod 777` にしたり所有者を一括変更したりしません。コンテナに必要な権限は起動時に確認します。以降は起動補助ツールがUUIDとext4を検査します。写真SSDを起動中に取り外すことまでは防げません。

fstabの誤記で問題が出た場合は、ローカル画面の復旧モード等で追加した1行を修正します。バックアップファイルで全体を戻す前に、他の変更が入っていないか確認してください。
