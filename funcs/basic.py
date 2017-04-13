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

############# BASIC START 基础服务部署

@roles('basic')
@task
def basic_deploy():
  info = env.info
  with cd("/opt"):
    # 变量
    ip = env.host

    # sysctl 调整
    run("""
echo 'kernel.shmall = 4294967296
net.netfilter.nf_conntrack_max = 1000000
kernel.unknown_nmi_panic = 0
kernel.sysrq = 0
fs.file-max = 1000000
vm.swappiness = 10
fs.inotify.max_user_watches = 10000000
net.core.wmem_max = 327679
net.core.rmem_max = 327679
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
fs.notify.max_queued_events = 3276792
net.ipv4.neigh.default.gc_thresh1 = 2048
net.ipv4.neigh.default.gc_thresh2 = 4096
net.ipv4.neigh.default.gc_thresh3 = 8192
vm.overcommit_memory=1
net.core.somaxconn = 512
#net.ipv6.conf.all.disable_ipv6 = 1' >> /etc/sysctl.conf
sysctl -p || echo "执行异常！"
""")

    # limits调整
    run("""
echo '* - nofile 1000000
* - nofile 1000000
* - core unlimited
* - stack 10240
* - noproc 1000000' > /etc/security/limits.conf

echo '
*          -    nproc     1000000
root       -    nproc     unlimited
' > /etc/security/90-noproc.conf
""")

    # selinux调整
    run("""
getenforce
setenforce 0
sed -i 's:SELINUX=.*:SELINUX=disabled:g' /etc/selinux/config
""")

    # crontab mailto调整
    run("""
sed -i 's:MAILTO=.*:MAILTO="":g' /etc/crontab
/etc/init.d/crond reload
""")

    # 时间同步
    run("""
echo 123
#yum install -y ntp
#chkconfig ntpd on
        """)

    # transparent调整
    run("""
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo "echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled " >> /etc/rc.local
        """)

    # 安全，关防火墙
    run("""
iptables -t filter -F
chkconfig iptables off
""")

    # 创建账户
    run(
      """  id %s && echo "Account Already Exist!" || useradd  --home=/opt/machtalk   --comment="one key deploy"  %s """ % (
        info['services']['basic']['normalUserName'], info['services']['basic']['normalUserName']))
    run(""" echo "%s" |passwd --stdin %s """ % (info['services']['basic']['normalUserPass'], info['services']['basic']['normalUserName']))

    # 基础软件安装
    # run(" yum install -y telnet rsync wget sysstat")

    # jdk安装
    run('yum remove -y java* java-*-openjdk && echo "openjdk卸载！" || echo "opendjk已卸载！"')
    put(env.local_softdir + "jdk-7u79-linux-x64.rpm", "~/")
    run('rpm -Uvh ~/jdk-7u79-linux-x64.rpm && echo "jdk安装完成！" || echo "jdk已经安装过了！"')

    # sudoers 配置
    run("""  echo '%s    ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/%s"""%(info['services']['basic']['normalUserName'],info['services']['basic']['normalUserName']))

    '''
    # java 如果安装不成功,可以在  rpm -Uvh之后
    alternatives --install /usr/bin/java java /usr/java/jdk1.7.0_79/bin/java 1
    alternatives --install /usr/bin/javac javac /usr/java/jdk1.7.0_79/bin/javac 1
    alternatives --install /usr/bin/jar jar /usr/java/jdk1.7.0_79/bin/jar 1
    '''

    # 修改i18n
    run("""
    sed -i 's:LANG=.*:LANG="zh_CN.UTF-8":g'  /etc/sysconfig/i18n

    # 建立machtalk cron文件
    touch /etc/cron.d/machtalk
    """)
