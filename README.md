# gitpull_server.py

Backlog の [Git Web フック][article1] を利用して、サーバ上での git pull を自動化するスクリプトです。
Web サーバとして動作して Backlog からのリクエストを待ち受けます。

Apache などの既存の Web サーバ上で動くアプリケーションではなく専用の Web サーバとして動作するため、
任意のユーザで実行させることができ、
git pull する際のパーミッションの問題を回避できます。

ポートを開ける必要があるため本番環境には不向きです。
開発サーバで git pull の手間を省く用途を想定しています。

みんな大好き Python 製です。

# セットアップ

3段階に分けて説明します。

## 1. とりあえず動かすとこまで

python の 2 系がインストールされてることを確認して下さい。

	$ python -V
	Python 2.7.3

python モジュール [bottle][] と [daemon][] をインストールします。

[bottle][] は pip でインストール。

	$ pip install bottle

[daemon][] の方は pip で入るバージョンが古いので、Web サイトからtarball をダウンロードしてインストールして下さい。

	$ curl -O https://pypi.python.org/packages/source/p/python-daemon/python-daemon-1.5.5.tar.gz
	$ tar xf python-daemon-1.5.5.tar.gz
	$ cd python-daemon-1.5.5
	$ python setup.py install

gitpull_server.py の設定ファイルを書きます。 `config.json.sample` をコピーして、

	$ cp config.json.sample config.json

環境に合わせて修正します。

	$ vim config.json
	{
	    "git_command": "/usr/bin/git",                  // gitコマンドのパス
	    "server_port": 56789,                           // 待受けるポート番号
	    "logfilename": "/tmp/gitpull.log",              // ログファイル
	    "error_logfilename": "/tmp/gitpull.err",        // エラーログファイル
	    "repositories": {                               // リポジトリの設定（複数指定可）
	        "repository1": "/path/to/git/repository",   //   "リポジトリ名": "リポジトリのディレクトリパス" のように書きます
	        "repository2": "/another/git/repository"
	    },
	    "email" {
	        "from_address": "hoehoe@hoehoe.com"         // git pull 失敗時に飛ばすメールのFROMアドレス
	    }
	}

試しに起動してみます。↓のように表示されればOK。Ctrl-C で終了。

	$ ./gitpull_server.py config.json
	Bottle v0.11.6 server starting up (using WSGIRefServer())...
	Listening on http://MonBookAir.local:56789/
	Hit Ctrl-C to quit.

## 2. git pull させてみる

POST リクエストに応えてちゃんと git pull してくれるかも実験しましょう。

GITリポジトリへの書き込み権限のあるユーザで起動します（作業者自身が書き込める場合は普通に起動します）。

	$ sudo -u user1 ./gitpull_server.py config.json
	Bottle v0.11.6 server starting up (using WSGIRefServer())...
	Listening on http://MonBookAir.local:56789/
	Hit Ctrl-C to quit.

別のシェルを立ち上げて、curl コマンドでリクエストを投げます。
"your\_email\_address@example.com" というGITアカウントが "repository1" リポジトリにコミットしたと想定すると、こんな感じ。

	$ EMAIL=your_email_address@example.com
	$ REPOSITORY=repository1
	$ PORT=56789
	$ curl -d payload="%7B%22before%22%3A%22%22%2C%22ref%22%3A%22refs/heads/develop%22%2C%22after%22%3A%22%22%2C%22repository%22%3A%7B%22description%22%3A%22%22%2C%22url%22%3A%22%22%2C%22name%22%3A%22${REPOSITORY}%22%7D%2C%22revisions%22%3A%5B%7B%22message%22%3A%22%22%2C%22modified%22%3A%5B%22%22%5D%2C%22id%22%3A%22%22%2C%22author%22%3A%7B%22name%22%3A%22%22%2C%22email%22%3A%22${EMAIL}%22%7D%2C%22url%22%3A%22%22%2C%22timestamp%22%3A%22%22%7D%5D%7D" http://$(hostname):${PORT}/gitpull

サーバを立ち上げた方のシェルに↓のようなメッセージが出ていればOK。

	$ sudo -u user1 ./gitpull_server.py config.json
	Bottle v0.11.6 server starting up (using WSGIRefServer())...
	Listening on http://MonBookAir.local:56789/
	Hit Ctrl-C to quit.

	repository: repository1
	directory: /path/to/git/repository
	committer: your_email_address@example.com
	192.168.12.16 - - [01/Nov/2013 20:15:17] "POST /gitpull HTTP/1.1" 200 0

## 3. Backlog の Git Web フック経由で動作させる

gitpull_server.py をデーモンとして立ち上げてしまいましょう。
`-d` オプションを付けて起動するだけ。

	$ sudo -u user1 ./gitpull_server.py config.json -d

そしたら[ここ][article1]や[ここ][article2]を参考に、
Backlog の Git Web フックに URL を登録します。
登録する URL は

**http://＜GITリポジトリのあるサーバ名＞:＜設定したポート番号＞/gitpull**

です。これで準備完了。

試しに、別のマシンでリポジトリに対して何かコミットして git push してみて下さい。
変更がサーバ上のリポジトリに自動で反映されていれば成功です。


# 停止するには

kill しちゃって下さい。

	$ pkill -f gitpull_server


# 参考
- [Git Webフック｜Backlogを使いこなそう｜どこでもプロジェクト管理バックログ][article1]
- [サルでも分かるGit Webフック入門 | Backlogブログ][article2]
- [Bottle: Python Web Framework](http://bottlepy.org/docs/dev/)
- [python-daemon 1.5.5 : Python Package Index](https://pypi.python.org/pypi/python-daemon/)

[article1]: http://www.backlog.jp/howto/userguide/userguide1710.html "Git Webフック｜Backlogを使いこなそう｜どこでもプロジェクト管理バックログ"
[article2]: http://www.backlog.jp/blog/2013/05/gitwebhook-for-monkey.html "サルでも分かるGit Webフック入門 | Backlogブログ"
[bottle]: http://bottlepy.org/docs/dev/ "Bottle: Python Web Framework"
[daemon]: https://pypi.python.org/pypi/python-daemon/ "python-daemon 1.5.5 : Python Package Index"
