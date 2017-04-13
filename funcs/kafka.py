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

############## KAFKA

@task
@roles("kafka")
def kafka_putfile():
    put(env.local_softdir + "kafka_2.12-0.10.2.0.tar.gz", env.remote_dir)

@task
@roles("kafka")
def kafka_deploy():
    pass

@task
@roles("kafka")
def kafka_clean():
    # 数据加工
    ## 搞到servers配置串
    kafkaConfigString = ""
    kafkaConfigString += """
    num.network.threads=3
    num.io.threads=8
    socket.send.buffer.bytes=102400
    socket.receive.buffer.bytes=102400
    socket.request.max.bytes=104857600
    num.partitions=1
    num.recovery.threads.per.data.dir=1
    log.retention.hours=168
    log.segment.bytes=1073741824
    log.retention.check.interval.ms=300000
    zookeeper.connection.timeout.ms=6000
        """

    kafka_hosts = ""
    kafkaListNumber = 1
    for ip in info['services']['mariadb']['servers']:
        # print ip
        # ip = "IP-" + ip.replace(".", "-")
        # kafkaConfigString += """server.%s=zk%s:2888:3888\n""" % (zkListNumber,zkListNumber)
        # zk_hosts += """
        # %s  zk%s"""%(ip,zkListNumber)
        # zkListNumber += 1
        pass
    ## 搞到myid，主要采用 bo.ips中查找当前的ip的位置，然后+1即可得到myid
    myid = info['services']['mariadb']['servers'].index(env.host)
    myid = myid + 1
    print myid
    ## 更新到hosts文件
    kafkaConfigString += """
    broker.id=%s
        """ % myid
    kafkaConfigString += """
    zookeeper.connect=192.168.0.2:2181,192.168.0.3:2181,192.168.0.4:2181
    log.dirs=/opt/machtalk/kafka/kafkalogs/
        """

    # 开始部署
    run("echo 'start deploy kafka'")
    # put(Const.SOURCE_DIR+"zookeeper-3.4.7", Const.DEST_DIR)
    #put(Const.SOURCE_DIR + "kafka_2.12-0.10.2.0.tar.gz", Const.DEST_DIR)
    run("tar xzf ./kafka_2.12-0.10.2.0.tar.gz")

    with cd(env.remote_dir):
        # kafka日志目录部署
        run(""" mkdir -p "./logs/kafka/" || echo "kafka日志目录已经存在" """)

        # kafka部署
        run("chown -R machtalk:machtalk kafka_2.12-0.10.2.0")
        run("ln -s kafka_2.12-0.10.2.0 kafka || echo '软连接已经存在了！'")
        run("mkdir -p ./kafka/kafkalogs || echo  'kafka日志目录已经存在!' ")

        # kafka配置写入
        run("""
    echo '%s' > ./kafka/config/server.properties
    """ % kafkaConfigString)

        # kafka启动
        run("chmod a+x ./kafka/bin/*.sh")
        run("cd ./kafka/bin && ./kafka-server-start.sh -daemon ../config/server.properties")

        # 测试
        run("cat ./kafka/config/server.properties")


    '''
    # 伟大的注释
    '''