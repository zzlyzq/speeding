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
@roles('openssh')
def openssh_7_5_upgrade():
    put(env.local_softdir+"openssh-7.5p1.tar.gz","/usr/local/src/")
    with cd("/usr/local/src"):
        run("""
cp -rf /etc/ssh /etc/ssh_bak
yum install -y gcc openssl-devel pam-devel rpm-build
cd /usr/local/src/
tar -zxvf openssh-7.5p1.tar.gz
cd openssh-7.5p1
./configure --prefix=/usr --sysconfdir=/etc/ssh --with-pam --with-zlib --with-md5-passwords
make -j 2
make install
cp -f ./sshd_config /etc/ssh/sshd_config
echo 'UsePAM yes' >> /etc/ssh/sshd_config
echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
service sshd reload && service sshd restart
chkconfig sshd on
    """)
