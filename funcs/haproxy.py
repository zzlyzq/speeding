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

@task
@roles("haproxy")
def haproxy_putfile():
    put(env.local_softdir+"haproxy.tar.gz",env.remote_dir)

@task
@roles("haproxy")
def haproxy_deploy():
    with cd(env.remote_dir):
        run("""
        tar xvf haproxy.tar.gz
        """)

@task
@roles("haproxy")
def haproxy_restart():
    with cd(env.remote_dir):
        run("""
        ./haproxy.init restart || echo "重启异常！"
        """)

@task
@roles("haproxy")
def haproxy_clean():
    with cd(env.remote_dir):
        run("""
        ps aux | grep haproxy | grep -v grep | awk '{print $2}' | xargs -i kill -9 {}
        ./haproxy.init restart || echo "重启异常！"
        """)