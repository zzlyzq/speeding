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

############# MGMT START 管理机器部署

@task
@roles('mgmt')
def files_upload():
  #filenames=[ 'addons.tar.gz', 'erlang.tar.gz', 'haproxy.tar.gz', 'mariadb-10.1.16-linux-x86_64.tar.gz', 'mq.tar.gz', 'openfalcon.tar.gz', 'rd.tar.gz', 'solrcloud.tar.gz', 'cloudera-manager-el6-cm5.5.0_x86_64.tar.gz', 'fastdfs.tar.gz', 'kafka_2.12-0.10.2.0.tar.gz', 'mongodb-linux-x86_64-2.6.11.tar.gz', 'nginx.tar.gz', 'rabbitmq_server-3.6.5.tar.gz', 'redis-2.8.23.tar.gz', 'zookeeper-3.4.7.tar.gz', 'CDH-5.5.0-1.cdh5.5.0.p0.8-el6.parcel', 'CDH-5.5.0-1.cdh5.5.0.p0.8-el6.parcel.sha', 'others' ]
  filenames=[ 'addons.tar.gz' ]
  for filename in filenames:
    # TODO 如果dst dir 不存在，那么就自动创建
    put(env.local_softdir+filename,env.remote_softdir)