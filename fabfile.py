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
execfile("/opt/3rd/funcs/addons.py")
execfile("/opt/3rd/funcs/basic.py")
execfile("/opt/3rd/funcs/cdh.py")
execfile("/opt/3rd/funcs/fdfs.py")
execfile("/opt/3rd/funcs/haproxy.py")
execfile("/opt/3rd/funcs/kafka.py")
execfile("/opt/3rd/funcs/keepalived.py")
execfile("/opt/3rd/funcs/mariadb.py")
execfile("/opt/3rd/funcs/mgmt.py")
execfile("/opt/3rd/funcs/mongo.py")
execfile("/opt/3rd/funcs/rabbitmq.py")
execfile("/opt/3rd/funcs/redis.py")
execfile("/opt/3rd/funcs/zookeeper.py")
execfile("/opt/3rd/funcs/shell.py")
execfile("/opt/3rd/funcs/ops.py")

# 如果需要打印log，取消下行的注释
logging.basicConfig(level=logging.WARN)

# 定义三台服务器

## 基础设施服务_root
t="root@192.168.0.186:22"
t_monitor="root@192.168.0.82:22"
t_fdfs_1="root@192.168.0.96:22"
t_fdfs_2="root@192.168.2.45:22"
t_redis_1="root@192.168.1.27:22"
t_redis_2="root@192.168.3.78:22"
t_mongo_1="root@192.168.1.89:22"
t_mongo_2="root@192.168.3.237:22"
t_mongo_3="root@192.168.1.143:22"
t_rabbitmq_1="root@192.168.1.138:22"
t_rabbitmq_2="root@192.168.3.249:22"
t_mariadb_1="root@10.0.5.30:22"
t_mariadb_2="root@10.0.6.30:22"
t_zookeeper_1="root@192.168.1.75:22"
t_zookeeper_2="root@192.168.3.28:22"
t_zookeeper_3="root@192.168.1.188:22"
t_keepalived_1=""
t_keepalived_2=""
t_monitor="root@192.168.0.82:22"

## 业务服务_machtalk
m="machtalk@192.168.0.186:22"
m_fdfs_1="machtalk@192.168.0.96:22"
m_fdfs_2="machtalk@192.168.2.45:22"
m_redis_1="machtalk@192.168.1.27:22"
m_redis_2="machtalk@192.168.3.78:22"
m_mongo_1="machtalk@192.168.1.89:22"
m_mongo_2="machtalk@192.168.3.237:22"
m_mongo_3="machtalk@192.168.1.143:22"
m_rabbitmq_1="machtalk@192.168.1.138:22"
m_rabbitmq_2="machtalk@192.168.3.249:22"
m_mariadb_1="machtalk@10.0.5.30:22"
m_mariadb_2="machtalk@10.0.6.30:22"
m_zookeeper_1="machtalk@192.168.1.75:22"
m_zookeeper_2="machtalk@192.168.3.28:22"
m_zookeeper_3="machtalk@192.168.1.188:22"
m_keepalived_1=""
m_keepalived_2=""
m_monitor="machtalk@192.168.0.82:22"

## 业务服务_root
t_api_1="root@192.168.0.92:22"
t_api_2="root@192.168.2.245:22"
t_ls_1="root@192.168.0.17:22"
t_ls_2="root@192.168.2.185:22"
t_cs_1="root@192.168.0.48:22"
t_cs_2="root@192.168.2.14:22"
t_bm_1="root@192.168.0.241:22"
t_cm_1="root@192.168.1.238:22"
t_cm_2="root@192.168.3.81:22"
t_xcloudmq_1="root@192.168.1.149:22"
t_xcloudmq_2="root@192.168.3.55:22"
t_xcloudmq_3="root@192.168.1.96:22"
t_xcloudmq_4="root@192.168.3.102:22"

## 业务服务_machtalk
m_api_1="machtalk@192.168.0.92:22"
m_api_2="machtalk@192.168.2.245:22"
m_ls_1="machtalk@192.168.0.17:22"
m_ls_2="machtalk@192.168.2.185:22"
m_cs_1="machtalk@192.168.0.48:22"
m_cs_2="machtalk@192.168.2.14:22"
m_bm_1="machtalk@192.168.0.241:22"
m_cm_1="machtalk@192.168.1.238:22"
m_cm_2="machtalk@192.168.3.81:22"
m_xcloudmq_1="machtalk@192.168.1.149:22"
m_xcloudmq_2="machtalk@192.168.3.55:22"
m_xcloudmq_3="machtalk@192.168.1.96:22"
m_xcloudmq_4="machtalk@192.168.3.102:22"

# define the comment for each machine  
#env.comments = {
#  t: "managent server",
#}

# 定义三台服务器的密码
env.passwords = {
    t:"sdf",
    m:"sdf",
    t_monitor:"sdf",
    t_fdfs_1:"sdf",
    t_fdfs_2:"sdf",
    m_fdfs_1:"123123",
    m_fdfs_2:"123123",
    t_redis_1:"123123",
    t_redis_2:"123123",
    m_redis_1:"123123",
    m_redis_2:"123123",
    t_mongo_1:"",
    t_mongo_2:"",
    t_mongo_3:"",
    m_mongo_1:"",
    m_mongo_2:"",
    m_mongo_3:"",
    t_rabbitmq_1: "",
    t_rabbitmq_2: "",
    m_rabbitmq_1: "",
    m_rabbitmq_2: "",
    t_zookeeper_1: "",
    t_zookeeper_2: "",
    t_zookeeper_3: "",
    m_zookeeper_1: "",
    m_zookeeper_2: "",
    m_zookeeper_3: "",
    t_mariadb_1:"",
    t_mariadb_2:"",
    m_mariadb_1:"",
    m_mariadb_2:"",
}

env.roledefs = {
        'mgmt': [t],
        #'basic': [t,t_fdfs_1,t_fdfs_2],
        #'basic': [t_redis_1,t_redis_2],
        #'basic': [t_mongo_1,t_mongo_2,t_mongo_3, t_rabbitmq_1,t_rabbitmq_2,t_zookeeper_1,t_zookeeper_2,t_zookeeper_3],
        #'basic': [t_monitor,t_mongo_3,t_rabbitmq_2],
        #'basic': [ t,t_fdfs_1,t_fdfs_2,t_redis_1,t_redis_2,t_mongo_1,t_mongo_2,t_mongo_3, t_rabbitmq_1,t_rabbitmq_2,t_zookeeper_1,t_zookeeper_2,t_zookeeper_3,t_api_1, t_api_2, t_ls_1, t_ls_2, t_cs_1, t_cs_2, t_bm_1, t_cm_1, t_cm_2, t_xcloudmq_1, t_xcloudmq_2, t_xcloudmq_3, t_xcloudmq_4 ],
        'all_t': [ t,t_monitor,t_fdfs_1,t_fdfs_2,t_redis_1,t_redis_2,t_mongo_1,t_mongo_2,t_mongo_3, t_rabbitmq_1,t_rabbitmq_2,t_zookeeper_1,t_zookeeper_2,t_zookeeper_3,t_api_1, t_api_2, t_ls_1, t_ls_2, t_cs_1, t_cs_2, t_bm_1, t_cm_1, t_cm_2, t_xcloudmq_1, t_xcloudmq_2, t_xcloudmq_3, t_xcloudmq_4 ],
        'all_m': [ m,m_monitor,m_fdfs_1,m_fdfs_2,m_redis_1,m_redis_2,m_mongo_1,m_mongo_2,m_mongo_3, m_rabbitmq_1,m_rabbitmq_2,m_zookeeper_1,m_zookeeper_2,m_zookeeper_3,m_api_1, m_api_2, m_ls_1, m_ls_2, m_cs_1, m_cs_2, m_bm_1, m_cm_1, m_cm_2, m_xcloudmq_1, m_xcloudmq_2, m_xcloudmq_3, m_xcloudmq_4 ],
        #'all_m': [ m ],
        'fdfs': [m_fdfs_1,m_fdfs_2],
        'redis': [m_redis_1,m_redis_2],
        'mongo': [ m_mongo_1, m_mongo_2, m_mongo_3 ],
        'rabbitmq': [m_rabbitmq_1,m_rabbitmq_2],
        'zookeeper': [m_zookeeper_1,m_zookeeper_2,m_zookeeper_3],
        'mariadb': [m_mariadb_1,m_mariadb_2],
        'keepalived': [ t_keepalived_1, t_keepalived_2 ],
        'cdh': [],
        'ops': [t_monitor],
        'jump': [t],
        }

# 定义一些环境变量，没有也无所谓，小细节
#env.sdir="/data/soft/soft/"
#env.ddir="/opt/machtalk/"
env.disable_known_hosts=True
env.abort_on_prompts=True
env.skip_bad_hosts = True
env.remote_interupt = True
env.warn_only = True
env.eagerly_disconnect = True
env.key_filename="./key"
#env.gateway=t
env.keepalive = 1

# 定义一些常量
## 本地软件目录
env.local_softdir="/opt/software/"
## 远端软件目录
env.remote_softdir="/opt/software/"
## 远端家目录
env.remote_dir="/opt/machtalk/"

# 需要一个json，描述场景中的变量
confJson = {
  'clusterName': "qingyunTest",
  'clusterType': "cluster",
  'servers': [ 'x.x.x.x', 'x.x.x.x.', 'x.x.x.x', 'x.x.x.x' ],
  #'rootpass': '',
  #'managementServer': "x.x.x.x",
  'services': {
          'basic': {
            'normalUserName': 'machtalk',
            'normalUserPass': '123123',
          },
            'keepalived': {
                'servers' : [ '1.1.1.1','1.1.1.2' ],
                'vipaddress': "1.1.1.3",
                'netcard': "eth1",
            },
          'zookeeper': {
            'servers': [ '192.168.1.75', '192.168.3.28', '192.168.1.188' ],
            'usrname': 'machtalk',
            'pwd': '123123',
            'useroot': 0,
            'zkclientport': '1812'
          },
          'mariadb': {
            'servers': [ '10.0.5.30', '10.0.6.30' ],
            'usrname': 'machtalk',
            'pwd': '123123',
            'useroot': 0,
            'usrname_replication': 'repli',
            'pwd_replication': 'repli'
          },
          'redis' :{
            'servers': [ '192.168.1.27', '192.168.3.78' ],
            'pwd': "123123",
            'pwd_masterauth': "123123",
          },
          'rabbitmq': {
            'servers': [ '192.168.1.138', '192.168.3.249' ],
            'usrname': "machtalk",
            'pwd': "123123",
          },
          'fdfs': {
            'servers': [ '192.168.0.96', '192.168.2.45' ],
            'storages': [
                        [ '192.168.0.96', '192.168.2.45' ],
                      ],
            'trackers': [ '192.168.0.96', '192.168.2.45' ],
            'nginxs': [ '192.168.0.96', '192.168.2.45' ]
          },
          'mongo': {
            'usrname': 'machtalk',
            'pwd': '123',
            'useroot': 0,
            'usrname_view': 'machtalk2',
            'pwd_view': '123123',
            # For 监控调用
            'port': '20000', 
            # # [0]－代表configserver [1]－代表mongos_server [2]－代表shards_server [3]－代表所有服务器，用于分配hosts
            'servers': [
                    [ "192.168.1.89", "192.168.3.237", "192.168.1.143" ], # config server
                    [ "192.168.1.89", "192.168.3.237", "192.168.1.143" ], # mongos
                    [ "192.168.1.89", "192.168.3.237", "192.168.1.143" ], # shard server
                    [ "192.168.1.89", "192.168.3.237", "192.168.1.143" ]  # all server
            ],
            'shardtotal': 3,
          },
          'cdh': {
              'servers': [ "172.25.0.3", "172.25.0.4" , "172.25.0.5" ],
              'dbip': "xx.x.x.x.",
              'dbusrname': "x.x.x.x",
              'dbpwd': "x.x.x.x"
          }
  }
}

# 把json unicode转成str的函数
def byteify(input):
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key,value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

print json.dumps(confJson,ensure_ascii=False).encode('utf-8')
env.info = json.loads(json.dumps(confJson,ensure_ascii=False),encoding='utf-8')
env.info = byteify(env.info)

############# list info
@task
@roles("basic")
def info_list():
    info = env.info
    print "zk 账号和密码信息"
    print info['services']['zookeeper']['usrname']
    print info['services']['zookeeper']['pwd']
    print info['services']['zookeeper']['zkclientport']

    print "redis 账号和密码信息"
    print info['services']['redis']['pwd']

    print "rabbitmq账号密码信息："
    print info['services']['rabbitmq']['usrname']
    print info['services']['rabbitmq']['pwd']

    print "mongo管理员账号和密码："
    print info['services']['mongo']['usrname']
    print info['services']['mongo']['pwd']

    print "mongo view账号和密码"
    print info['services']['mongo']['usrname_view']
    print info['services']['mongo']['pwd_view']

############# 获取SHELL

@task
def shell(cmd=None):
  myhost=eval(env.host)
  env.host_string=myhost
  env.password=env.passwords[myhost]
  env.key_filename="./key"
  if cmd is None:
    print "即将登陆服务器: %s"%(env.host_string)
    fabric.operations.open_shell()
  else:
    print "即将在服务器执行命令: %s"%(env.host_string)
    run(cmd)

############## transfer file
@task
@roles("jump")
def transfer_file():
  put("/opt/software/python.2.7.12.tar.gz","/tmp/")

############# machtalk ssh pubkey deploy
@task
@roles('basic')
def sshpubkey_deploy():
   # deploy machtalk account pub key
   run("""
mkdir /opt/machtalk/.ssh
cat << 'EOF'  > /opt/machtalk/.ssh/authorized_keys
your key
EOF

chown -R machtalk:machtalk /opt/machtalk/.ssh
chmod 700 /opt/machtalk/.ssh
""")
