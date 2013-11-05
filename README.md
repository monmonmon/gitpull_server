# gitpull_server.py

Github の [Post-Receive Hooks][github1] や Backlog の [Git Web フック][backlog1] は、
git pull をフックとして任意のURLに POST リクエストを送信させられるサービスです。

gitpull_server.py は、このリクエストを受信して git pull を自動実行するサーバアプリケーションです。

既存の Web サーバ（Apache 等）上で動くアプリケーションではなく、独立した Web サーバとして動作するため、任意のユーザで実行させることができ、UNIX のパーミッションの問題を回避できます。

みんな大好き Python 製です。

# 注意点

- パスワードなしで git pull 出来るリポジトリのみ対応（今のところ）。パスワードなし公開鍵で SSH で git pull するようにして下さい。
- 専用のポートを開ける必要があるため、使いどころには注意して下さい。開発サーバで git pull の手間を省く用途を想定しています。
- ポート番号さえ分かれば誰でも git pull を実行させられてしまうというリスクがあります。

# セットアップ

3段階に分けて説明します。

## 1. Python 環境の準備

Python の2系がインストールされていなければインストールして下さい。

	$ python -V
	Python 2.7.3

Python モジュールのパッケージ管理システム **pip** をインストールします。easy_install（これも Python 付属のパッケージ管理システム）でインストール出来ます。

    $ easy_install pip

一部パッケージのアップデートが必要かも？（pip install -r でエラーが出たので…）

    $ pip install -U distribute
    $ pip install -U setuptools

pip を使って、動作に必要なモジュールを自動でインストール出来ます。
インストールするのは [GitPython][], [PyYAML][], [bottle][], [python-daemon][] の4つ。

    $ pip install -r packages.txt

ちなみに、インストール済みのパッケージ一覧は `pip list` で。

	$ pip list



### 2. 動かしてみる

gitpull_server.py の設定ファイルを書きます。
`config.yml.sample` を参考に修正して下さい。

	$ cp config.yml.sample config.yml
	$ vim config.yml

試しに起動してみましょう。GIT リポジトリで git pull 可能なユーザで起動して下さい。

	$ sudo -u user1 ./gitpull_server.py config.yml      # "user1" ユーザで起動する場合
	Bottle v0.11.6 server starting up (using WSGIRefServer())...
	Listening on http://MonBookAir.local:56789/                 ←登録するURL
	Hit Ctrl-C to quit.

作業者自身が git pull 出来る場合は sudo 不要。

	$ ./gitpull_server.py config.yml
	Bottle v0.11.6 server starting up (using WSGIRefServer())...
	Listening on http://MonBookAir.local:56789/                 ←登録するURL
	Hit Ctrl-C to quit.

画面にこんな風に表示されればOKです。

矢印で示したように、URL が表示されていると思います。
この URL を後で [Post-Receive Hooks][github1] (Github) や [Git Web フック][backlog1] (Backlog) に登録するのですが、
とりあえずブラウザで開いてみて下さい。

ブラウザで開くと、テスト用フォームが表示されます。
このフォームを使って、Github や Backlog を介さずに、Web Hook の POST リクエストをシミュレートして実際に git pull が動作するかどうかテストすることが出来ます。

select でリポジトリを選択して、ボタンをクリックして下さい。

ブラウザに success と表示されれば成功です。



## 3. Backlog の Git Web フック経由で動作させる

gitpull_server.py をデーモンとして立ち上げてしまいましょう。
`-d` オプションを付けて起動するだけ。

	$ sudo -u user1 ./gitpull_server.py config.yml -d
	
	or
	
	$ ./gitpull_server.py config.yml -d

ログファイルが設定ファイルの logfilename に設定したパスに作られます。

	$ cat /tmp/gitpull_server.log

そしたら Web Hook に URL を登録します。

Github の場合は[このへん][github1]、
Backlog の場合は[このへん][backlog1]を参考に、
さっきの URL を登録して下さい。

これでセットアップ完了です。

試しに、 gitpull_server.py に設定したのとは別のリポジトリから何かコミットして git push してみて下さい。
変更がサーバ上のリポジトリに自動で反映されていれば成功です。


# デーモンを停止するには

`-k` オプションで kill 出来ます。

	$ ./gitpull_server.py config.yml -k


# 参考
- [Git Webフック｜Backlogを使いこなそう｜どこでもプロジェクト管理バックログ][backlog1]
- [サルでも分かるGit Webフック入門 | Backlogブログ][backlog2]
- [Bottle: Python Web Framework](http://bottlepy.org/docs/dev/)
- [python-daemon 1.5.5 : Python Package Index](https://pypi.python.org/pypi/python-daemon/)

[github1]: https://help.github.com/articles/post-receive-hooks "Post-Receive Hooks · GitHub Help"
[backlog1]: http://www.backlog.jp/howto/userguide/userguide1710.html "Git Webフック｜Backlogを使いこなそう｜どこでもプロジェクト管理バックログ"
[backlog2]: http://www.backlog.jp/blog/2013/05/gitwebhook-for-monkey.html "サルでも分かるGit Webフック入門 | Backlogブログ"
[GitPython]: https://github.com/gitpython-developers/GitPython "gitpython-developers/GitPython"
[bottle]: http://bottlepy.org/docs/dev/ "Bottle: Python Web Framework"
[python-daemon]: https://pypi.python.org/pypi/python-daemon/ "python-daemon 1.5.5 : Python Package Index"
[PyYAML]: http://pyyaml.org/ "PyYAML"
