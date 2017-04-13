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

env.falcon_dir="/data/openfalcon/open-falcon/"
@task
@roles("ops")
def elk_e_putfile():
    put(env.local_softdir+"openfalcon.tar.gz", env.falcon_dir)

@task
@roles("ops")
def falcon_deploy():
    with cd(env.falcon_dir):
        run("""
                tar xzf openfalcon.tar.gz
        """)

@task
@roles("ops")
def falcon_restart():
    pass

@task
@roles("ops")
def falcon_clean():
    pass

