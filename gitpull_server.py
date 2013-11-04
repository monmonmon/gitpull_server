#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8

"""
gitpull_server.py

Backlog の [Git Web フック][article1] を利用して、サーバ上での git pull を自動化するスクリプトです。
Web サーバとして動作して Backlog からのリクエストを待ち受けます。

Apache などの既存の Web サーバ上で動くアプリケーションではなく専用の Web サーバとして動作するため、
任意のユーザで実行させることができ、UNIX のパーミッションの問題を回避できます。
"""

import os
import sys
import re
import json
import yaml
import urllib
from optparse import OptionParser
from bottle import route, get, post, run, template, request
from daemon import DaemonContext
import git

config = None

def sendmail(to_address, from_address, subject, message):
    """
    メール投げる
    """
    import smtplib
    from email.mime.text import MIMEText
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address
    s = smtplib.SMTP()
    s.connect()
    s.sendmail(from_address, [to_address], msg.as_string())
    s.close()

def register_repositories(config):
    """
    リポジトリ名→リポジトリディレクトリのマップを作成

    各リポジトリディレクトリの origin の url 設定から、リポジトリ名を取得する
    """
    config['__repositories'] = {}
    print "registering repositories..."
    for directory in config['repositories']:
        try:
            repo = git.Repo(directory)
            url = repo.remotes.origin.url
            match = re.search("""/([^/]+)\.git$""", url)
            repository_name = match.group(1)
            config['__repositories'][repository_name] = directory
            print >> sys.stderr, "  {0}: {1}".format(repository_name, directory)
        except git.exc.InvalidGitRepositoryError as e:
            raise Exception(directory + ": git リポジトリではありません。")
        except AttributeError as e:
            raise Exception(directory + ": .git/config からのリポジトリ名の取得に失敗しました。")
    return config

@get('/')
def process_get():
    """
    GETリクエストを処理する
    """
    fp = open('get.html.tmpl', 'rb')
    html = fp.read()
    fp.close()
    options = ['<option>{r}</option>'.format(r=r) for r in config['__repositories']]
    html = html.replace('%OPTIONS%', ''.join(options))
    return html

@post('/')
def process_post():
    """
    POSTリクエストを処理する
    """
    try:
        # リクエストからリポジトリ名、コミットした人のEMAILアドレスを抜き出す
        payload = request.forms['payload']
        data = json.loads(payload)
        email_address = data['revisions'][0]['author']['email']
        repository_name = data['repository']['name']
        # リポジトリ名からGITディレクトリを取得
        repository_directory = config['__repositories'].get(repository_name)
        if not repository_directory:
            print >> sys.stderr, "ignoring unregistered repository: " + repository_name
            return
        print >> sys.stderr, "repository: " + repository_name
        print >> sys.stderr, "directory: " + repository_directory
        print >> sys.stderr, "committer: " + email_address
        # origin を git pull
        repo = git.Repo(repository_directory)
        repo.remotes.origin.pull()
        return """<!DOCTYPE html>
<html>
  <head>
    <title>gitpull_server.py</title>
  </head>
  <body>
    success :)
  </body>
</html>
"""
    except Exception as e:
        print >> sys.stderr, "ERROR: ", e

def main():
    """
    メイン処理
    設定をロードしてWebサーバを起動する
    """
    # コマンドラインオプションをパーズ
    optionparser = OptionParser(usage="""Usage: %prog <config file>""")
    optionparser.add_option("-d", dest="daemon", action="store_true", help="run as a daemon")
    (options, args) = optionparser.parse_args()
    if len(args) != 1:
        optionparser.print_help()
        sys.exit(1)
    configfile = args[0]
    # 設定ファイルをロード
    stream = file(configfile, "r")
    global config
    config = yaml.load(stream)
    stream.close()
    config = config['git_server']
    # リポジトリ名→リポジトリディレクトリのマップを作成
    config = register_repositories(config)
    # ホスト名を取得
    hostname = os.uname()[1]
    # Webサーバ起動
    if options.daemon:
        # デーモンとして起動
        dc = DaemonContext(
            #stdout=open(config['logfilename'], 'w+'),
            stdout=open(config['logfilename'], 'w+'),
            stderr=open(config['error_logfilename'], 'w+')
            )
        with dc:
            print >>sys.stderr, os.getpid()
            run(host=hostname, port=config['server_port'])
    else:
        # そのまま起動
        run(host=hostname, port=config['server_port'])

if __name__ == '__main__':
    main()
