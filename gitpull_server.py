#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8

"""
hoehoe
"""

import os
import sys
import commands
import json
import yaml
from optparse import OptionParser
from bottle import route, get, post, run, template, request
from daemon import DaemonContext

configfile = "config.yml"

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

def gitpull(repository_directory, email_address):
    """
    指定したディレクトリ下で git pull を実行する。
    git pull に失敗したらコミットした人にアラートメールを送信する。
    @param str repository_name リポジトリ名
    @param str email_address   コミットした人のEMAILアドレス
    """
    # リポジトリのディレクトリに移動
    os.chdir(repository_directory)
    # git pull実行
    (status, git_message) = commands.getstatusoutput(config['git_command'] + ' pull');
    if 0 != status:
        sendmail(email_address, config['from_address'], 'Git pull failed', git_message)

@post('/gitpull')
def process_gitpull():
    """
    /git/pull へのPOSTリクエストを処理する
    """
    try:
        # リクエストからリポジトリ名、コミットした人のEMAILアドレスを抜き出す
        payload = request.forms['payload']
        data = json.loads(payload)
        email_address = data['revisions'][0]['author']['email']
        repository_name = data['repository']['name']
        repository_directory = config['repositories'][repository_name]
        print >> sys.stderr, "repository: " + repository_name
        print >> sys.stderr, "directory: " + repository_directory
        print >> sys.stderr, "committer: " + email_address
        # gitpull
        gitpull(repository_directory, email_address)
    except Exception as e:
        print >> sys.stderr, "ERROR: ", e

def main():
    """
    メイン処理
    設定を読んでWebサーバを起動する
    """
    global config
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
    config = yaml.load(stream)
    stream.close()
    config = config['git_server']
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
