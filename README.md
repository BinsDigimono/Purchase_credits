# Purchase_credits

教授からこっそり単位を買えるサイト（ネタ）です。Django で作りました。

## 機能

- ログイン（学生と教授）
- 科目一覧・検索・詳細
- カートと申し込み（1科目1つまで）
- 申込履歴
- 教授は管理画面から出品できて、売れた履歴も見られる
- 学生と教授の DM（LINE っぽくした）、教授側に「AIで断る」ボタン
- ログインしてない人にはメンテナンス中のページしか見えない

## 動かし方

```
cd Purchase_credits
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

環境変数 `DJANGO_DEBUG=1` を入れないと CSS が読み込まれません。
PowerShell なら `$env:DJANGO_DEBUG=1` です（`set` だと効かなかった）。

http://127.0.0.1:8000/ を開くとメンテナンス中の画面が出るので、下のアカウントでログインしてください。

| ユーザ名 | 区分 | パスワード |
| --- | --- | --- |
| `t23cs001` / `t23cs002` | 学生 | `demo-pass-1234` |
| `prof.yamada` / `prof.suzuki` | 教授 | `demo-pass-1234` |

管理画面は `/staff-console/` です。教授のアカウントで入れます。

## テスト

```
cd Purchase_credits
python manage.py test
```

GitHub Actions でも push のたびに同じテストが動きます。

## メモ

- 単位を売ってるサイトだとバレないように、トップはメンテナンス画面に見せかけたログインフォームにして、ログインしてないときは他のページを全部 404 にしました。ログイン画面に飛ばすとページがあることがバレるので。
- 買えるかどうかのチェックは `shop/views.py` の `purchase_error()` にまとめてます。
- 申し込んだときの科目名や値段は `OrderItem` にコピーして保存してます。あとで科目を編集しても履歴が変わらないようにするため。
- 「AIで断る」は今は決まった文章からランダムに選んでるだけです。

## TODO

- 「AIで断る」を本物の AI にする
- 科目一覧のページ分け
- 同時に買われたときに在庫がずれるのを直す
- 単位を取る
