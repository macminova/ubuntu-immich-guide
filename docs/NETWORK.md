# 接続経路と公開範囲

公開資料の基本方針は、認証されたTailscale内からアクセスし、インターネットへImmichやSSHを直接公開しないことです。

| 区間 | 参考記録での方式 |
|---|---|
| スマートフォン・PCからサーバー | 認証されたTailscale端末からのアクセス |
| HTTPSの入口 | Tailscale Serve |
| ServeからImmich | サーバー内のループバック接続 |
| コンテナ間 | Docker内部ネットワーク |
| 外部からのDB直接接続 | 提供しない |

Tailscale Serveと、インターネット公開のためのFunnelを混同しないでください。実際のアクセス許可はtailnetのユーザー・端末・ポリシーでも管理します。
[Tailscale Serve公式](https://tailscale.com/docs/reference/tailscale-cli/serve)

## 過去の設定との違い

運用記録には、当初のLAN限定構成と、その後のTailscale限定構成が混在しています。新しい記録では「Dockerが全IPv4アドレスで2283番をバインドし、DOCKER-USERで直接アクセスを拒否」「Serveはtailnet限定でループバックの2283番へ接続」とされています。今回、実サーバーの現在のルールを読み取ったわけではありません。

この公開準備では、その方式をコピペ用のファイアウォール設定として提供しません。新規構築向けにはループバック限定バインドなどの代案も比較し、Dockerの版・iptables/nftables・IPv6を含めて実機試験してから決定します。

Dockerの公開ポートはUFWの想定と異なる経路を通る場合があります。「UFWが有効だからDockerのポートも非公開」とは判断しないでください。
[Docker公式](https://docs.docker.com/engine/network/packet-filtering-firewalls/)

ルーターのポート転送、UPnP、Funnel、ファイアウォール無効化は、この構成の前提にしません。

Tailscaleは外部サービスを含む接続基盤です。この方式を「外部通信が一切ない完全オフライン環境」とは案内しません。
