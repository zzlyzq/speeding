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
@roles("keepalived")
def keepalived_putfile():
    put(env.local_softdir+"keepalived.conf.tar.gz",env.remote_dir)

@task
@roles("keepalived")
def keepalived_deploy():
    # 安装软件
    run("""
    yum install keepalived ipvsadm -y
    """)
    # 配置和script脚本解压释放
    run("""
    cd /etc
    mv keepalived keepalived.bak || echo "移动文件夹异常！"
    tar xzvf keepalived.conf.tar.gz
    """)
    # 配置文件上去
    run("""
cat << 'EOF' > /etc/keepalived/keepalived.conf
! Configuration File for keepalived

global_defs {
   router_id LVS_DEVEL
}

vrrp_script chk_haproxy {
    script "/etc/keepalived/check_haproxy.sh"
    interval 10
    #weight -2
}

vrrp_instance LAN_1 {
    unicast_src_ip %s
    unicast_peer {
	    %s
    }
    state BACKUP
    interface eth1
    virtual_router_id 51
    nopreempt
    priority 100
    advert_int 10
    authentication {
        auth_type PASS
        auth_pass 1111
    }
    virtual_ipaddress {
	    %s dev %s
    }

    track_script {
        chk_haproxy
    }
   #notify_master /etc/keepalived/scripts/start_haproxy.sh
   #notify_stop   /etc/keepalived/scripts/stop_haproxy.sh

}EOF"""%(env.host,info['services']['keepalived']['servers'].remove(env.host)[0], info['services']['keepalived']['vipaddress'],info['services']['keepalived']['netcard']))