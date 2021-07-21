# user-avatar-bot

jao Minecraft Server での Admin, Moderator, Regular, Verified のユーザー顔スキンを絵文字化します。

## 仕様

`main.py` を実行すると、以下を実施します。

1. Admin, Moderator, Regular, Verified のユーザーを取得
2. コンフィグファイルから絵文字サーバの ID を取得、サーバにある絵文字の一覧を取得
3. プレイヤー名と UUID の紐づけファイル(`linking-player-uuid.json`)から紐づけ一覧を取得 (2回目実行以降・既保存の場合)
4. プレイヤー UUID と顔スキン画像の紐づけファイル(`linking-uuid-hashes.json`)からハッシュ値一覧を取得 (2回目実行以降・既保存の場合)
5. 絵文字の ID とその絵文字があるサーバの ID の紐づけファイル(`linking-emoji-guild-id.json`)からハッシュ値一覧を取得 (2回目実行以降・既保存の場合)
6. プレイヤー UUID と絵文字の ID の紐づけファイル(`linking-uuid-emoji-id.json`)からハッシュ値一覧を取得 (2回目実行以降・既保存の場合)
7. ユーザー毎に新しいユーザーか・ユーザー名が変更されているか・スキンが変更されているかをチェックする
8. 必要に応じて絵文字の新規作成・絵文字名の変更・絵文字を再作成する
