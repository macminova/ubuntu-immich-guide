# Tailscaleとスマートフォンを接続する

[入口に戻る](START-HERE.md)。Immichのpingとループバック待受を先に確認します。

Tailscaleは外部サービスです。登録・端末認証・接続調整のためTailscaleと認証プロバイダーに通信します。接続状況により暗号化された通信が中継サーバーを通る場合もあります。「外部通信ゼロ」の構成ではありません。写真の保存先は自分のサーバーです。利用条件を確認してから導入してください。

## Ubuntuへ導入する

以下はUbuntu 26.04用の[公式パッケージ手順](https://pkgs.tailscale.com/stable/)です。取得先は `pkgs.tailscale.com` です。既存Tailscaleがある場合は上書きせず設定を先に確認します。

```bash
set -o pipefail
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/resolute.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/resolute.tailscale-keyring.list | sudo tee /etc/apt/sources.list.d/tailscale.list >/dev/null
sudo apt update
sudo apt install tailscale
sudo tailscale up
tailscale status
```

認証URLを自分のブラウザーで開き、自分のアカウントでサーバーを登録します。URLや認証キーをSNSに貼りません。管理画面で登録端末を確認します。アカウントには多要素認証を設定し、他人とのtailnet共有やACLの緩和はしません。

## HTTPSの入口を作る

```bash
sudo tailscale serve --bg http://127.0.0.1:2283
tailscale serve status
```

HTTPS有効化を求められたら案内を読み、自分のtailnetに対して有効化します。証明書発行に伴いホスト名が公開証明書ログに載り得るため、ホスト名に個人名を使わないでください。表示された**自分のHTTPS URL**を控えます。2283のポート番号を付け足しません。[Serve公式](https://tailscale.com/docs/reference/tailscale-cli/serve)も確認してください。

Serveはtailnet向けです。`tailscale funnel` はインターネット公開なので使いません。tailnet参加者なら到達できる可能性があるため、共有アカウントを使わずImmich側の認証も維持します。

## Windows・iPhoneで開く

1. [Tailscale公式ダウンロード](https://tailscale.com/download)から各端末にアプリを導入します。iPhoneはそこから公式App Storeへ進みます。
2. サーバーと同じ自分のアカウントでログインし、接続を有効にします。
3. ブラウザーで先ほどのHTTPS URLを開きます。
4. 最初のImmichユーザーは管理者になります。自分が先に登録し、長く固有のパスワードを設定します。
5. [Immich公式](https://docs.immich.app/install/post-install/)のリンクからモバイルアプリを導入し、同じURLを指定します。サーバー版との互換性を確認します。
6. 個人情報のない試験画像を1枚アップロードし、別端末で表示・ダウンロードできることを確かめます。
7. iPhoneの自動バックアップは試験専用アルバムだけを選びます。いきなり写真ライブラリ全体を選びません。

携帯回線に切り替えてもTailscale接続中に表示できるか確認します。Tailscaleを切るとアクセスできなくなるのがこの構成の想定です。失敗してもルーターのポートを開放しないでください。基本編のImmichはOS再起動後に手動起動が必要です。
