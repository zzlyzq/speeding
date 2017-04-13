#!/usr/bin/python
# -*- coding: utf-8 -*
from fabric.api import *
from fabric.context_managers import *
from fabric.contrib.console import confirm
from fabric.contrib.files import *
from fabric.contrib.project import rsync_project
import fabric.operations
import time,os
import logging
import base64
from getpass import getpass
import json
import sys

# 定义一些常量
## 本地软件目录
env.local_softdir="/opt/software/"
## 远端软件目录
env.remote_softdir="/opt/software/"
## 远端家目录
env.remote_dir="/opt/machtalk/"


############## MARIADB


@task
@roles('mariadb')
def mariadb_10_1_22_putfile():
    # 上传文件
    fileNeedTransfer = []
    fileNeedTransfer.append("mariadb-10.1.22-linux-x86_64.tar.gz")
    for tarFileName in fileNeedTransfer:
        put("%s%s" % (env.local_softdir,tarFileName), env.remote_dir)

@task
@roles('mariadb')
def mariadb_10_1_22_deploy():
    with cd(env.remote_dir):
        # 从fabric拿到当前ip
        ip = env.host
        info = env.info

        # 判断目录是否存在，如果存在就退出
        run(""" [ -e "./mariadb" ] && exit 1 || echo '开始部署mariadb！' """)

        # 上传文件
        fileNeedTransfer = []
        fileNeedTransfer.append("mariadb-10.1.22-linux-x86_64.tar.gz")
        for tarFileName in fileNeedTransfer:
            #put("%s%s" % (Const.SOURCE_DIR, tarFileName), Const.DEST_DIR)
            run("tar xzf %s" % tarFileName)
            #run("rm -f %s" % tarFileName)

        # 做软链
        run("""ln -s ./mariadb-10.1.22-linux-x86_64 ./mariadb && echo '软链创建成功！' || echo '软链已经存在！' """)

        # 修改环境变量
        run('''
            sed -i '/mariadb/d' ~/.bashrc
            sed -i '$a export PATH=%s/mariadb/bin:$PATH' ~/.bashrc
            ''' % (env.remote_dir))

        # 配置文件
        conf_mariadb = """
    [server]
    [mysqld_safe]
    log-error=/opt/machtalk/logs/mariadb/error.log
    [mysqld]
    skip-name-resolve
    log-bin=mysql-bin
    server-id=1
    sync_binlog=1
    innodb_flush_log_at_trx_commit=1
    binlog_format=mixed
    character_set_server=utf8
    slow_query_log=on
    long_query_time=2
    log-error=/opt/machtalk/logs/mariadb/error.log
    key_buffer_size=256
    max_allowed_packet=4M
    thread_stack=256K
    table_cache=128K
    sort_buffer_size=6M
    read_buffer_size=4M
    wait_timeout=86400
    thread_concurrency=8
    max_connections=100000
    lower_case_table_names=1
    user=machtalk
    basedir=/opt/machtalk/mariadb/
    datadir=/opt/machtalk/mariadb/data/
    socket=/opt/machtalk/mariadb/mysql.sock
    pid_file=/opt/machtalk/mariadb/mysql.pid
    lc-messages-dir=/opt/machtalk/mariadb/share/english/
    relay_log=relay-bin
    [galera]
    [embedded]
    [mariadb]
    [mariadb-10.1]
            """
        run(""" echo '%s' > ./mariadb/my.cnf """ % conf_mariadb)

        # 创建必须目录和文件
        run("""
            mkdir -p /opt/machtalk/logs/mariadb/ || echo '目录创建异常！'
            mkdir -p /opt/machtalk/mariadb/data/ || echo '目录创建异常！'
            touch /opt/machtalk/mariadb/mysql.pid
            """)

        # 数据库初始化
        run("cd ./mariadb && ./scripts/mysql_install_db --defaults-file=/opt/machtalk/mariadb/my.cnf")

        # 启动前，启动脚本需要做些修改
        run("""cd ./mariadb/ && sed -i 's:^basedir=$:basedir=/opt/machtalk/mariadb/:g' ./support-files/mysql.server """)
        run("""cd ./mariadb/ && sed -i '1,$ s:if $bindir/mysqladmin ping >/dev/null 2>&1; then:if test -e $mysqld_pid_file_path;then:' /opt/machtalk/mariadb/support-files/mysql.server
    """)

        # 启动服务
        run(""" /opt/machtalk/mariadb/support-files/mysql.server restart || echo  "服务启动异常！" """)

        # 设置账号和密码
        run(""" . ~/.bashrc ; mysql -h 127.0.0.1 -u root -e "grant all privileges on *.* to %s@'%s' identified by '%s' with grant option;"  """ % (info['services']['mariadb']['usrname'], "%", info['services']['mariadb']['pwd']))
        run(""" . ~/.bashrc ; mysql -h 127.0.0.1 -u root -e "grant all privileges on *.* to %s@'%s' identified by '%s' with grant option;"  """ % (info['services']['mariadb']['usrname'], "localhost", info['services']['mariadb']['pwd']))
        #run(""" . ~/.bashrc ; mysql -h 127.0.0.1 -u root -e "grant all privileges on *.* to %s@'%s' identified by '%s' with grant option;"  """ % ("root", "%", info['services']['mariadb']['pwd']))

        # 开始集群配置喽
        # 如果是master,我们就执行一些命令
        if ip == info['services']['mariadb']['servers'][0]:
            print info['services']['mariadb']['usrname_replication']
            print info['services']['mariadb']['pwd_replication']
            print "I am runing with the master role"
            run("""
                    sed -i 's:server-id=.*:server-id=1:g' ./mariadb/my.cnf
                    ./mariadb/support-files/mysql.server restart || echo '重启异常!'
                """)
            run("""
                source ~/.bashrc;
                mysql -h 127.0.0.1 -u root -e "GRANT REPLICATION SLAVE ON *.* TO '%s'@'%s' IDENTIFIED BY '%s'; FLUSH PRIVILEGES; FLUSH TABLES WITH READ LOCK;SHOW MASTER STATUS;"
                """ % (info['services']['mariadb']['usrname_replication'], "%", info['services']['mariadb']['pwd_replication']))

        # 如果是slave,我们就执行一些命令
        if ip == info['services']['mariadb']['servers'][1]:
            print "I am runing with the slave role"
            run("""
                    sed -i 's:server-id=.*:server-id=2:g' ./mariadb/my.cnf
                    ./mariadb/support-files/mysql.server restart || echo '重启异常!'
                """)
            run("""
                source ~/.bashrc;
                mysql -h 127.0.0.1 -u root -e "STOP SLAVE;CHANGE MASTER TO MASTER_HOST='%s', MASTER_USER='%s', MASTER_PASSWORD='%s', MASTER_LOG_FILE='mysql-bin.000007', MASTER_LOG_POS=659; start slave; show slave status\G;"
                """ % (info['services']['mariadb']['servers'][0], info['services']['mariadb']['usrname_replication'], info['services']['mariadb']['pwd_replication']))


    '''
    # 备注
    #测试可以使用  两下回车就好了，因为本身毕竟没有设置账号和密码
    mysql -h 127.0.0.1 -u root -p

    # 今儿才知道，原来mariadb也是需要依赖一个devel
    yum install -y libaio-devel
    '''

@task
@roles('mariadb')
def mariadb_clean():
    with cd(env.remote_dir):
        run(""" ps aux | grep mariadb | grep -v grep | awk '{print $2} | xargs -i kill -9 {} '  """)
        run("rm -rf mariadb-10.1.22-linux-x86_64 mariadb")
