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

############# 获取SHELL

@task
def shell(cmd=None):
  myhost=eval(env.host)
  env.host_string=myhost
  env.password=env.passwords[myhost]
  if cmd is None:
    print "即将登陆服务器: %s"%(env.host_string)
    fabric.operations.open_shell()
  else:
    print "即将在服务器执行命令: %s"%(env.host_string)
    run(cmd)