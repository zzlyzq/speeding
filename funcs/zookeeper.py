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


############## ZOOKEEPER

@task
@roles('zookeeper')
def zookeeper_putfile():
    # 上传文件
    fileNeedTransfer = []
    fileNeedTransfer.append("zookeeper-3.4.7.tar.gz")
    for tarFileName in fileNeedTransfer:
        put("%s%s" % (env.local_softdir,tarFileName), env.remote_dir)

@task
@roles('zookeeper')
def zookeeper_deploy():
    ip = env.host
    info = env.info

    # 数据加工
    ## 搞到servers配置串
    zkConfigString = ""
    zk_hosts = ""
    zkListNumber = 1
    for ip in info['services']['zookeeper']['servers']:
        # print ip
        #ip = "IP-" + ip.replace(".", "-")
        zkConfigString += """server.%s=zk%s:2888:3888\n""" % (zkListNumber,zkListNumber)
        zk_hosts += """
%s  zk%s"""%(ip,zkListNumber)
        zkListNumber += 1
    ## 搞到myid，主要采用 bo.ips中查找当前的ip的位置，然后+1即可得到myid
    myid = info['services']['zookeeper']['servers'].index(env.host)
    myid = myid+1
    print myid
    ## 更新到hosts文件
    sudo("""
sed -i 's:zk*$::g' /etc/hosts
cat << 'EOF' >> /etc/hosts
%s
EOF
    """%zk_hosts)

    # 开始部署
    run("echo 'start deploy zookeeper'")
    #put(Const.SOURCE_DIR+"zookeeper-3.4.7", Const.DEST_DIR)
    run("tar xzf ./zookeeper-3.4.7.tar.gz")

    with cd(env.remote_dir):
        # zk日志目录部署
        run(""" mkdir -p "./logs/zookeeper/" || echo "zk日志目录已经存在" """)

        # zk部署
        run("chown -R machtalk:machtalk zookeeper-3.4.7")
        run("ln -s zookeeper-3.4.7 zookeeper || echo '软连接已经存在了！'")

        # zk配置
        conf_zk="""
tickTime=2000
initLimit=10
syncLimit=5
dataDir=/opt/machtalk/zookeeper/data
clientPort=%s
maxClientCnxns=100000
        """%(info['services']['zookeeper']['zkclientport'])
        conf_zk += zkConfigString

        run("""
        sed -i "/server.*=/d" ./zookeeper/conf/zoo.cfg
        echo "%s" >> ./zookeeper/conf/zoo.cfg
        echo %s > ./zookeeper/data/myid
        """%(conf_zk,myid))

        # 清空过去的数据
        run(""" rm -rf ./zookeeper/data/version-2""")

        # 日志轮转命令
        run("""
sed -i 's#ZOO_LOG_DIR=.*#ZOO_LOG_DIR="$ZOOBINDIR/../logs"#g' /opt/machtalk/zookeeper/bin/zkEnv.sh
sed -i 's#ZOO_LOG4J_PROP=.*#ZOO_LOG4J_PROP="INFO,ROLLINGFILE"#g' /opt/machtalk/zookeeper/bin/zkEnv.sh

sed -i 's#MaxFileSize=.*#MaxFileSize=100MB#g' /opt/machtalk/zookeeper/conf/log4j.properties
sed -i 's/#log4j.appender.ROLLINGFILE.MaxBackupIndex=10/log4j.appender.ROLLINGFILE.MaxBackupIndex=10/g' /opt/machtalk/zookeeper/conf/log4j.properties
        """)

        # zk启动
        run("chmod a+x ./zookeeper/bin/*.sh")
        run("./zookeeper/bin/zkServer.sh stop || echo 'zookeeper进程不存在!' ")
        run("./zookeeper/bin/zkServer.sh start")

        # 判断，如果当前id等于ips的长度，那么就是最后一台机器，我们需要连接到zk进行命令部署
        ## 先搞到密码
        import hashlib
        import base64
        ## 然后执行zk添加权限命令
        if myid == len(info['services']['zookeeper']['servers']):
            pass
            #run(""" ./zookeeper/bin/zkCli.sh -server localhost:%s create /newconfig "" digest:%s:%s:rwadc"""%(bo.zkclientport,bo.usrname,base64.b64encode(hashlib.sha1("%s:%s"%(bo.usrname,bo.pwd)).digest())))
            # 应该使用如下的一行，将设置的账号和密码进行部署验证，但是拿到pwd需要进过sha1和digest的验证，过去是采用openssl命令，但是目标机器不一定有openssl，打算用python实现，TODO
            #run(""" ./zookeeper/bin/zkCli.sh create /newconfig "" digest:%s:%s:rwadc"""%(bo.usrname,bo.pwd))

        # 测试
        run("cat ./zookeeper/conf/zoo.cfg")

    '''
    # 测试
    addauth digest ops:123123
    ls /newconfig

    Kr5w5aopF3RSTesZ

    addauth digest machtalk:Kr5w5aopF3RSTesZ
    '''

@task
@roles('zookeeper')
def zookeeper_clean():
    with cd(env.remote_dir):
        run(" ps aux | grep java | grep '/opt/machtalk/zookeeper' | grep -v grep | awk '{print $2}' | xargs -i kill -9 {}  ")
        run("rm -rf ./zookeeper zookeeper-3.4.7")
