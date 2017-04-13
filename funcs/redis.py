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

############# REDIS START

@roles('redis')
@task
def redis_deploy():
    with cd(env.remote_dir):
        # 基本变量
        info = env.info

        # 判断目录是否存在，如果存在就退出
        run(""" [ -e "./redis" ] && exit 1 || echo '开始部署redis！' """)

        # 上传文件
        fileNeedTransfer = []
        fileNeedTransfer.append("redis-2.8.23.tar.gz")
        for tarFileName in fileNeedTransfer:
            put("%s%s" % (env.local_softdir, tarFileName), env.remote_dir)
            run("tar xzf %s" % tarFileName)
            run("rm -f %s" % tarFileName)

        # 做软链
        run("chown -R machtalk:machtalk redis*")
        run("""ln -s ./redis-2.8.23 ./redis && echo '软链创建成功！' || echo '软链已经存在！' """)

        # 文件权限修改
        run("""
            chown -R machtalk:machtalk redis
            chmod a+x ./redis/utils/*
            chmod a+x ./redis/src/redis-server
            chmod a+x ./redis/src/redis-sentinel
            """)

        # 准备一些变量
        ip = env.host
        masterFlag = 0
        myListNumber = info['services']['redis']['servers'].index(ip)
        if myListNumber % 2 == 0:
            print "I am running as a master node."
            masterListNumber = myListNumber
            masterFlag = 1
        else:
            print "I am running as a slave node"
            masterListNumber = myListNumber - 1

        masterIP = info['services']['redis']['servers'][masterListNumber]

        # 配置文件修改
        conf_6379 = """
daemonize yes
pidfile /opt/machtalk/redis/redis_6379.pid
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 0
loglevel notice
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /opt/machtalk/redis/data
slave-serve-stale-data yes
slave-read-only yes
repl-diskless-sync no
repl-diskless-sync-delay 5
repl-disable-tcp-nodelay no
slave-priority 100
appendonly no
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
lua-time-limit 5000
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 0
notify-keyspace-events ""
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-entries 512
list-max-ziplist-value 64
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit slave 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
aof-rewrite-incremental-fsync yes
logfile /opt/machtalk/redis/log/redis.log
requirepass %s
maxclients 100000
masterauth %s
            """ % (info['services']['redis']['pwd'], info['services']['redis']['pwd_masterauth'])
        if masterFlag == 0:
            conf_6379 += """
    slaveof %s 6379
                """ % (masterIP)

        conf_26379 = ""
        conf_26379 += """
    daemonize yes
    port 26379
    logfile /opt/machtalk/redis/log/sentinel.log
    pidfile /opt/machtalk/redis/redis_26379.pid
    dir /opt/machtalk/redis
            """
        i = 0
        for j in info['services']['redis']['servers']:
            if i % 2 == 0:
                groupNumber = int(i / 2) + 1
                conf_26379 += """
    sentinel monitor group%s %s 6379 2
    sentinel down-after-milliseconds group%s 30000
    sentinel parallel-syncs group%s 1
    sentinel failover-timeout group%s 180000
    sentinel auth-pass group%s %s
                    """ % (groupNumber, j, groupNumber, groupNumber, groupNumber, groupNumber, info['services']['redis']['pwd'])
            i += 1

        # 开始写入
        run(""" echo '%s' > ./redis/6379.conf""" % (conf_6379))
        run(""" echo '%s' > ./redis/26379.conf""" % (conf_26379))

        # 关闭服务
        run("set -m; cd ./redis/utils/; ./my_redis stop || echo '服务已经关闭！' ")
        run("set -m; cd ./redis/utils/; ./my_sentinel stop || echo '服务已经关闭！' ")

        # 启动服务
        run("set -m; cd ./redis/utils/; ./my_redis start || echo '服务已经打开！' ")
        run("set -m; cd ./redis/utils/; ./my_sentinel start || echo '服务已经打开！' ")
    '''
            # 备注
            # 测试的话可以 telnet localhost 6379
            # 然后使用 auth xxx
            # incr a等命令去测试

            验证 telnet xx 26379
            master0:name=group1,status=ok,address=172.16.72.36:6379,slaves=1,sentinels=2

            # TODO 4个redis的时候还是有问题
    '''

@task
@roles('redis')
def redis_restart():
    with cd(env.remote_dir):
        run("chown -R machtalk:machtalk redis*")
        # 关闭服务
        #run("set -m; cd ./redis/utils/; ./my_redis stop || echo '服务已经关闭！' ")
        #run("set -m; cd ./redis/utils/; ./my_sentinel stop || echo '服务已经关闭！' ")
        run("""
        pid=`ps aux | grep redis-server | grep -v grep | awk "{print $2}"`
        kill -9 $pid
        """)
        run("""
        pid=`ps aux | grep redis-sentinel | grep -v grep | awk "{print $2}"`
        kill -9 $pid
        cd ./redis/ && rm -f *.pid
        """)

        # 启动服务
        run("set -m; cd ./redis/utils/; ./my_redis start || echo '服务已经打开！' ")
        run("set -m; cd ./redis/utils/; ./my_sentinel start || echo '服务已经打开！' ")
