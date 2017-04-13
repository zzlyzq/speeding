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

@roles("vmwareclient")
@task
def vmware_tool_deploy():
    put(env.local_softdir+"VMwareTools-9.4.5-1734305.tar.gz","/tmp/")
    run("""
           cd /tmp
           tar xzvf VMwareTools-9.4.5-1734305.tar.gz
           cd vmware-tools-distrib
           ./vmware-install.pl -d
            """)

@roles("vmwareserver")
@task
def vmware_ovftool_deploy():
    # 软件下载可以通过 http://ftp.tucha13.net/pub/software/VMware-ovftool-4.1.0/
    put(env.local_softdir+"vmware-ovftool.tar.gz","/vmfs/volumes/datastore1/")
    run("tar -xzf /vmfs/volumes/datastore1/vmware-ovftool.tar.gz -C /vmfs/volumes/datastore1/")
    run("sed -i 's@^#!/bin/bash@#!/bin/sh@' /vmfs/volumes/datastore1/vmware-ovftool/ovftool")
