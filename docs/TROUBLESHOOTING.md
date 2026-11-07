# 困ったとき

[入口に戻る](START-HERE.md)。エラーを飛ばして次へ進まず、写真・DBを消して解決しようとしないでください。

| 症状 | 確認と対応 |
|---|---|
| 写真SSDの検査でSTOP | `findmnt --mountpoint /mnt/photos` と `lsblk -f` を確認。UUID・ext4・接続を直す。検査を削除して起動しない |
| `.env` が既にある | 初期化の再実行は不要。既存環境でないか確認し、通常のpreflightを使う。パスワードを再生成しない |
| `!override` を解釈できない | Docker公式Compose 2.24.4以上が必要。タグを削って回避しない |
| 2283が全アドレス待受 | 他のComposeやoverride取り違えを調査。起動した本ガイドのサービスを停止し、ループバック設定を検査する |
| OS再起動で表示できない | 基本編は自動起動なし。SSD確認後にSTART-HEREの再起動後コマンドを実行する |
| Tailscale経由で開けない | ローカルping、端末双方のTailscale接続、Serve statusを順に確認。ポート開放・Funnelは不要 |
| 顔認識・意味検索が使えない | 基本編は機械学習を無効化しているため想定どおり |
| DB認証エラー | 既存DBと.envの組合せを確認。DBディレクトリ削除・パスワードの適当な変更は禁止 |
| 容量不足 | `df -h /mnt/photos /srv/immich-db` を確認。写真の手動削除やDocker volume pruneで解決しない |
| バックアップ中に失敗 | COMPLETEなしの回は未完了。元データを保ち、原因解消後に新しい回として保存する |

ローカルで状態を調べるには、作業ディレクトリで以下を使います。ログ・パスには個人情報やトークンが含まれ得ます。相談時は自分で伏せてください。

```bash
cd /opt/immich/compose
sudo docker compose ps
sudo docker compose logs --tail=80 immich-server database
```

`docker compose down -v`、DBディレクトリ削除、ディスク再フォーマット、セキュリティ機能無効化はこのガイドの復旧手段ではありません。
