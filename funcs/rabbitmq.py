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

############## MQ

@task
@roles('rabbitmq')
def rabbitmq_putfile():
    # 上传文件
    fileNeedTransfer = []
    fileNeedTransfer.append("rabbitmq_server-3.6.5.tar.gz")
    fileNeedTransfer.append("erlang.tar.gz")
    for tarFileName in fileNeedTransfer:
        put("%s%s" % (env.local_softdir,tarFileName), env.remote_dir)

@task
@roles('rabbitmq')
def rabbitmq_deploy():
    with cd(env.remote_dir):
        # 获取fabric传过来的变量
        ip = env.host
        info = env.info

        # 判断目录是否存在，如果存在就退出
        run(""" [ -e "./rabbitmq" ] && exit 1 || echo '开始部署rabbitmq！' """)

        # 根据变量获取
        ip = env.host
        ipListNumber = info['services']['rabbitmq']['servers'].index(ip) + 1
        serverName = "rabbit%s"%(ipListNumber)

        # 设置主机名
#        sudo("""
#cat << 'EOF' > /etc/sysconfig/network
#NETWORKING=yes
#HOSTNAME=%s
#EOF
#hostname %s
#        """%(serverName,serverName))

        # 设置hosts
        conf_hosts = ""
        itemNumber = 0
        for item in info['services']['rabbitmq']['servers']:
            conf_hosts += """
%s rabbit%s"""%(item, itemNumber + 1)
            itemNumber += 1
        sudo("""
            sed -i "/rabbit/d" /etc/hosts
            #service network restart
            echo '%s' >> /etc/hosts
        """%(conf_hosts))


        # 上传文件
        fileNeedTransfer = []
        fileNeedTransfer.append("rabbitmq_server-3.6.5.tar.gz")
        fileNeedTransfer.append("erlang.tar.gz")
        for tarFileName in fileNeedTransfer:
            #put("%s%s" % (Const.SOURCE_DIR,tarFileName), Const.DEST_DIR)
            run("tar xzf %s"%tarFileName)
            #run("rm -f %s"%tarFileName)

        # 做软链
        run("""ln -s ./rabbitmq_server-3.6.5 ./rabbitmq && echo '软链创建成功！' || echo '软链已经存在！' """)

        # 修改本机hostname 对于rabbitmq来说
        run('''
            sed -i '/RABBITMQ_NODENAME/d' ./rabbitmq/etc/rabbitmq/rabbitmq-env.conf || echo "异常，可能文件不存在！"
            echo 'RABBITMQ_NODENAME=rabbit@%s' >> ./rabbitmq/etc/rabbitmq/rabbitmq-env.conf
        '''%serverName)

        # erlang修改
        run(""" echo -n "KGGDOQPNUOBMMBGGVRCU" > ~/.erlang.cookie  """)
        run(""" chmod 600 ~/.erlang.cookie""")
        # 修改环境变量
        run('''
        sed -i '/rabbitmq/d' ~/.bashrc
        sed -i '$a export PATH=%s/rabbitmq/sbin:$PATH' ~/.bashrc
        '''%(env.remote_dir))

        # 修改权限
        run("chmod 755 ./rabbitmq/sbin/*")
        run("chmod 755 ./erlang/bin/*")
        run("chmod 755 ./erlang/lib/erlang/erts-7.3/bin/*")

        # 服务停止与启动
        run("set -m;./rabbitmq/sbin/rabbitmq-server -detached || echo '进程已经存在！'")

        # 添加插件
        run("./rabbitmq/sbin/rabbitmq-plugins enable rabbitmq_management || echo '插件安装异常！' ")

        if ipListNumber == 1:
            # 添加用户
            run("./rabbitmq/sbin/rabbitmqctl add_user %s %s || echo '123' "%(info['services']['rabbitmq']['usrname'],info['services']['rabbitmq']['pwd']) )

            #　创建vhost以及权限
            run("./rabbitmq/sbin/rabbitmqctl add_vhost /xcloud || echo 'vhost添加异常！' ")
            run("./rabbitmq/sbin/rabbitmqctl set_user_tags %s administrator || echo '123' "%info['services']['rabbitmq']['usrname'])
            run("""./rabbitmq/sbin/rabbitmqctl set_permissions -p /xcloud %s ".*" ".*" ".*" """%info['services']['rabbitmq']['usrname'] )
        else:
            # 加入集群
            run("""
                rabbitmqctl stop_app
                #rabbitmqctl join_cluster --ram rabbit@rabbit1
                rabbitmqctl join_cluster rabbit@rabbit1
                rabbitmqctl start_app
            """)

    '''
            # 备注
            # 可以查看15672端口
    http://192.168.3.133:15672
    '''

@task
@roles('rabbitmq')
def rabbitmq_clean():
    with cd(env.remote_dir):
        run(" ps aux | grep rabbitmq | grep -v grep | awk '{print $2}' | xargs -i kill -9 {} ")
        run("rm -rf erlang rabbitmq_server-3.6.5 rabbitmq")

@task
@roles('rabbitmq')
def rabbitmq_restart():
    with cd(env.remote_dir):
        run(" ps aux | grep rabbitmq | grep -v grep | awk '{print $2}' | xargs -i kill -9 {} 2>/dev/null")
        run("set -m;./rabbitmq/sbin/rabbitmq-server -detached || echo '进程已经存在！'")
