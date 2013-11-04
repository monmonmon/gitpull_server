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
import daemon
import lockfile
import git

config = None

def load_config_file(configfile):
    """
    設定ファイルをロード、チェック、デフォルト値補完する
    また、リポジトリディレクトリのリストからリポジトリ名→リポジトリディレクトリのマップを作成する
    """
    default_config = {
        'git_command': '/usr/bin/git',
        'port': 56789,
        'hostname': os.uname()[1],
        'logfilename': '/tmp/gitpull_server.log',
        'pidfilename': '/tmp/gitpull_server.pid',
        'repositories': [],
    }
    try:
        # yamlファイルからロード
        stream = file(configfile, "r")
        config = yaml.load(stream)
        stream.close()
        config = config['git_server']
        # 設定値をデフォルト値で補完＆型チェック
        for key, value in default_config.iteritems():
            if key not in config:
                config[key] = value
            elif type(config[key]) != type(value):
                # 型の不整合
                raise Exception('config parameter "{0}" should be {1}'.format(key, type(value)))
        # 詳細なチェック
        if not os.access(config['git_command'], os.X_OK):
            raise Exception('git command ' + config['git_command'] + ' is not executable')
        if not os.path.isdir(os.path.dirname(config['logfilename'])):
            raise Exception('log directory ' + os.path.dirname(config['logfilename']) + ' does not exist')
        if not os.path.isdir(os.path.dirname(config['pidfilename'])):
            raise Exception('pidfile directory ' + os.path.dirname(config['pidfilename']) + ' does not exist')
        if len(config['repositories']) == 0:
            raise Exception('repositories are not registered')
        # リポジトリ名→リポジトリディレクトリのマップを作成
        config['__repositories'] = {}
        for directory in config['repositories']:
            if not os.path.isdir(directory):
                raise Exception(directory + ': not a directory')
            try:
                repo = git.Repo(directory)
                url = repo.remotes.origin.url
                match = re.search("""/([^/]+)\.git$""", url)
                repository_name = match.group(1)
                config['__repositories'][repository_name] = directory
            except git.exc.InvalidGitRepositoryError as e:
                raise Exception(directory + ": not a git repository")
            except AttributeError as e:
                raise Exception(directory + ": failed to get the repository name from .git/config")
        return config
    except Exception as e:
        print "ERROR:", e
        return None

def kill_daemon():
    """
    実行中のデーモンをkillする
    """
    import signal
    pidfile = lockfile.FileLock(config['pidfilename'])
    if not pidfile.is_locked():
        return False
    with open(pidfile.lock_file, 'r') as pidfp:
        pid = int(pidfp.read())
    os.kill(pid, signal.SIGTERM)
    return True

@get('/')
def process_get():
    """
    GETリクエストを処理する
    """
    options = ['<option>{r}</option>'.format(r=r) for r in config['__repositories']]
    return config['get_response_template'].replace('%OPTIONS%', ''.join(options))

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
            print "ignoring unregistered repository: " + repository_name
            return
        print "repository: " + repository_name
        print "directory: " + repository_directory
        print "committer: " + email_address
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
        print "ERROR: ", e

def main():
    """
    メイン処理
    """
    # コマンドラインオプションをパーズ
    optionparser = OptionParser(usage="""Usage: %prog <config file>""")
    optionparser.add_option("-d", dest="daemon", action="store_true", help="run as a daemon")
    optionparser.add_option("-k", dest="kill", action="store_true", help="kill the running daemon")
    (options, args) = optionparser.parse_args()
    if len(args) != 1:
        optionparser.print_help()
        return 1
    # 設定ファイルをロード＆チェック
    global config
    config = load_config_file(args[0])
    if not config:
        return 1
    # killモード
    if options.kill:
        if kill_daemon():
            print "killed the daemon"
        else:
            print "daemon is not running"
        return 1
    # GETリクエストへのレスポンス用のHTMLテンプレートを読み込んでおく
    template_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'get.html.tmpl')
    with open(template_path, 'rb') as fp:
        config['get_response_template'] = fp.read()
    # ホスト名を取得
    hostname = os.uname()[1]
    # Webサーバ起動
    if options.daemon:
        # デーモンとして起動
        pidfile = lockfile.FileLock(config['pidfilename'])
        if pidfile.is_locked():
            print "daemon is already running. quit"
            return 1
        logfp = open(config['logfilename'], 'a')
        context = daemon.DaemonContext(
            pidfile = pidfile,
            stdout = logfp,
            stderr = logfp
            )
        with context:
            print "\nstart daemon (PID: {pid})".format(pid = os.getpid())
            # lockfileにpidを書き出す
            with open(context.pidfile.lock_file, 'w') as pidfp:
                print >>pidfp, os.getpid()
            # サーバ起動
            run(host=config['hostname'], port=config['port'])
    else:
        # そのまま起動
        run(host=config['hostname'], port=config['port'])

if __name__ == '__main__':
    main()
