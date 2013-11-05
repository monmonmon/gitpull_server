# gitpull_server.py

## これは何？

Github の [Post-Receive Hooks][github1] や Backlog の [Git Web フック][backlog1]（以降まとめて "Web Hook" とします）は、
git push をフックとして任意のURLに POST リクエストを送信させられるサービスです。

**gitpull_server.py** は、このリクエストを受信して git pull を自動実行するだけのシンプルなサーバアプリケーションです。

既存の Web サーバ（Apache 等）上で動くアプリケーションではなく、独立した Web サーバとして動作するため、任意のユーザで実行させることができ、UNIX のパーミッションの問題を回避できます。

みんな大好き Python 製です。



## 注意点

- パスワードなしで git pull 出来るリポジトリのみ対応。パスワードなし公開鍵で SSH で git pull するようにして下さい。。。
- 専用のポートを開ける必要があるため、本番環境とかには不向きだと思います。開発サーバでの開発中に git pull の手間を省く用途を想定しています。
- ポート番号さえ分かれば誰でも git pull を実行させられてしまうというリスクがあります。
リクエストの FROM アドレスでアクセス制限かけたらいいって話ですけどね… \_(:3｣∠)\_ そのうちやりますってば…
- 今のところ [Github](https://github.com/) と [Backlog](http://www.backlog.jp/) 管理のリポジトリにのみ対応しています。[Bitbucket](https://bitbucket.org/) も同様の機能を持ってるっぽいので対応したい（他にもありますか？）。
- git push のタイミングで git pull を単純に1回実行するだけなので、これに失敗した場合更新されません。メールなどのアラートもあがりません。要 merge な場合などは、ほっとけばいつまでも古いままです。手動で merge して下さい。
- リポジトリ毎に git pull 可能な UNIX ユーザが異なる場合（リポジトリAは monmon ユーザ所有だけどリポジトリBは apache ユーザ所有だ、とか）、gitpull_server.py を複数立ち上げる必要があります。

（これらは TODO リストでもあります）



## セットアップ

3段階に分けて説明します。

### 1. Python 環境の準備

Python の2系がインストールされていなければインストールして下さい。

	$ python -V
	Python 2.7.3

Python モジュールのパッケージ管理システム **pip** をインストールします。easy_install（これも Python 付属のパッケージ管理システム）でインストール出来ます。

    $ easy_install pip

一部パッケージのアップデートが必要かも？（pip install -r でエラーが出たので…）

    $ pip install -U distribute
    $ pip install -U setuptools

pip を使って、動作に必要なモジュールを自動でインストール出来ます。
インストールするのは [GitPython][], [Bottle][], [python-daemon][], [PyYAML][] の4つ。

    $ pip install -r packages.txt

ちなみにインストール済みのパッケージ一覧は `pip list` で。

	$ pip list



### 2. 動かしてみる

gitpull_server.py の設定ファイルを書きます。
`config.yml.sample` を参考に修正して下さい。

	$ cp config.yml.sample config.yml
	$ vim config.yml

試しに起動してみましょう。
対象 GIT リポジトリで git pull 可能なユーザで起動して下さい。

	$ ./gitpull_server.py config.yml
	Bottle v0.11.6 server starting up (using WSGIRefServer())...
	Listening on http://MonBookAir.local:56789/                 ←登録するURL
	Hit Ctrl-C to quit.

画面にこんな風に表示されればOKです。

矢印で示したように、URL が表示されていると思います。
この URL を後で Web Hook に登録するのですが、
とりあえずブラウザで開いてみて下さい。

ブラウザで開くと、テスト用フォームが表示されます。
このフォームを使って、Github や Backlog を介さずに、Web Hook の POST リクエストをシミュレートして実際に git pull が動作するかどうかテストすることが出来ます。

select でリポジトリを選択して、ボタンをクリックして下さい。

ブラウザに success と表示されれば成功です。



### 3. Web Hook 経由で動作させる

gitpull_server.py をデーモンとして立ち上げてしまいましょう。
`-d` オプションを付けて起動するだけ。

	$ ./gitpull_server.py config.yml -d

ログファイルが設定ファイルの logfilename に設定したパスに作られます。

	$ cat /tmp/gitpull_server.log

そしたら Web Hook に URL を登録します。

Github の場合は[このへん][github1]、Backlog の場合は[このへん][backlog1]を参考に、さっきの URL を登録して下さい。

これでセットアップ完了です。

試しに、 gitpull_server.py に設定したのと同じリポジトリを別のディレクトリに git clone して、そこから何かコミットして git push してみて下さい。
変更が元のリポジトリに自動で反映されていれば成功です☆



## デーモンを停止するには

`-k` オプションで kill 出来ます。

	$ ./gitpull_server.py config.yml -k

もしくは普通に kill しちゃって下さい。

	$ pkill -f gitpull_server



## ライセンス

Licensed under the [MIT](http://www.opensource.org/licenses/MIT) license.

Copyright 2013 Shimon Yamada



## 参考
- [Git Webフック｜Backlogを使いこなそう｜どこでもプロジェクト管理バックログ][backlog1]
- [サルでも分かるGit Webフック入門 | Backlogブログ][backlog2]
- [gitpython-developers/GitPython][GitPython]
- [Bottle: Python Web Framework][Bottle]
- [python-daemon 1.5.5 : Python Package Index][python-daemon]
- [PyYAML][PyYAML]

[github1]: https://help.github.com/articles/post-receive-hooks "Post-Receive Hooks · GitHub Help"
[backlog1]: http://www.backlog.jp/howto/userguide/userguide1710.html "Git Webフック｜Backlogを使いこなそう｜どこでもプロジェクト管理バックログ"
[backlog2]: http://www.backlog.jp/blog/2013/05/gitwebhook-for-monkey.html "サルでも分かるGit Webフック入門 | Backlogブログ"
[GitPython]: https://github.com/gitpython-developers/GitPython "gitpython-developers/GitPython"
[Bottle]: http://bottlepy.org/docs/dev/ "Bottle: Python Web Framework"
[python-daemon]: https://pypi.python.org/pypi/python-daemon/ "python-daemon 1.5.5 : Python Package Index"
[PyYAML]: http://pyyaml.org/ "PyYAML"
