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
@roles("falcon")
def falcon_putfile():
    put(env.local_softdir+"openfalcon.tar.gz", env.falcon_dir)

@task
@roles("falcon")
def falcon_deploy():
    with cd(env.falcon_dir):
        run("""
                tar xzf openfalcon.tar.gz

        """)

@task
@roles("ops")
def falcon_restart():
    run("""
   ps aux | grep supervisord | grep falcon | grep -v grep | awk '{print $2}' | xargs -i kill -9 {}
   /data/openfalcon/open-falcon/python/fabenv/bin/python /data/openfalcon/open-falcon/python/fabenv/bin/supervisord -c /data/openfalcon/open-falcon/supervisor/supervisord.conf
    """)

@task
@roles("ops")
def falcon_clean():
    pass

@task
@roles("all_t")
def falcon_agent_stop():
    run("""
        ps aux | grep falcon-agent | awk '{print $2}' | xargs -i kill -9 {}
        ps aux | grep ss.expand | awk '{print $2}' | xargs -i kill -9 {}
        ps aux | grep "machtalk/agent" | awk '{print $2}' xargs -i kill -9 {}
    """)

######### falcon agent

@roles("all_m")
@task
def falcon_agent_deploy():
    with cd(env.remote_dir):
        #run("echo a")
        put(env.local_softdir+"./falcon.agent.tar.gz",env.remote_dir)
        run("""
            ps aux | grep falcon-agent | grep -v grep | awk '{print $2}' | xargs -i kill {} || echo "异常！"
	    tar xvf falcon.agent.tar.gz
            sed -i 's:myip:%s:g' ./agent/cfg.json
            sed -i 's:serverip:%s:g' ./agent/cfg.json
            cd agent; ./control restart
        """%(env.host, "172.31.0.82"))

@roles("all_m")
@task
def falcon_agent_restart():
    with cd(env.remote_dir):
        run("""
            ps aux | grep falcon-agent | grep -v grep | awk '{print $2}' | xargs -i kill -9 {} || echo '异常！'
            cd ./agent; ./control restart
        """)

######### falcon  deploy ss.closewait

@roles("all_m")
@task
def falcon_agent_plugin_ssclosewait_deploy():
    with cd(env.remote_dir):
        run("mkdir -p ./agent/userdeinfe/ || echo '文件夹已经存在！'")
        put(env.local_softdir+"agent.userdefine/ss.closewait", env.remote_dir+"./agent/userdefine/")
        run("""
           chmod a+x ./agent/userdefine/ss.closewait 
           sed -i 's:myip:%s:g' ./agent/userdefine/ss.closewait
           # 部署定时任务 
           sudo sed -i '/ss.closewait/g' /etc/cron.d/machtalk
           sudo echo '* * * * * machtalk cd /opt/machtalk/agent/userdefine && ./ss.closewait' >> /etc/cron.d/machtalk
        """%(env.host))

########## falcon deploy redis
@roles("redis")
@task
def falcon_agent_plugin_redis_deploy():
    with cd(env.remote_dir):
        put(env.local_softdir+"./agent.userdefine/redis.check.py", env.remote_dir+"./agent/userdefine/")
        run("""
	   chmod a+x ./agent/userdefine/redis.check.py
           sed -i 's:myip:%s:g' ./agent/userdefine/redis.check.py
           # 部署定时任务 
           #cd /etc/cron.d && sudo sed -i '/redis.check.py/g' machtalk
           #cd /etc/cron.d && sudo echo '* * * * * machtalk cd /opt/machtalk/agent/userdefine && ./redis.check.py' >> machtalk
        """%(env.host))
        sudo("""
           cd /etc/cron.d && sudo sed -i '/redis.check.py/g' machtalk
           cd /etc/cron.d && sudo echo '* * * * * machtalk cd /opt/machtalk/agent/userdefine && ./redis.check.py' >> machtalk
        """)


########## falcon deploy fdfs

@roles("fdfs")
@task
def falcon_agent_plugin_fdfs_deploy():
    with cd(env.remote_dir):
        put(env.local_softdir+"./agent.userdefine/fdfs.check.py", env.remote_dir+"./agent/userdefine/")
        run("""
	   chmod a+x ./agent/userdefine/fdfs.check.py
           sed -i 's:myip:%s:g' ./agent/userdefine/fdfs.check.py
        """%(env.host))
        sudo("""
           cd /etc/cron.d && sudo sed -i '/fdfs.check.py/g' machtalk
           cd /etc/cron.d && sudo echo '* * * * * machtalk source ~/.bashrc ;cd /opt/machtalk/agent/userdefine && ./fdfs.check.py' >> machtalk
        """)


########## falcon deploy rabbitmq

@roles("rabbitmq")
@task
def falcon_agent_plugin_rabbitmq_deploy():
    with cd(env.remote_dir):
        put(env.local_softdir+"./agent.userdefine/rabbitmq.check.py", env.remote_dir+"./agent/userdefine/")
        run("""
	   chmod a+x ./agent/userdefine/rabbitmq.check.py
           sed -i 's:myip:%s:g' ./agent/userdefine/rabbitmq.check.py
           sed -i 's:myname:%s:g' ./agent/userdefine/rabbitmq.check.py
           sed -i 's:mypass:%s:g' ./agent/userdefine/rabbitmq.check.py
        """%(env.host,env.info['services']['rabbitmq']['usrname'],env.info['services']['rabbitmq']['pwd']))
        sudo("""
           cd /etc/cron.d && sudo sed -i '/rabbitmq.check.py/g' machtalk
           cd /etc/cron.d && sudo echo '* * * * * machtalk source ~/.bashrc ;cd /opt/machtalk/agent/userdefine && ./rabbitmq.check.py' >> machtalk
        """)

########## falcon deploy mongo

@roles("mongo")
@task
def falcon_agent_plugin_mongo_deploy():
    with cd(env.remote_dir):
        put(env.local_softdir+"./agent.userdefine/mongomon", env.remote_dir+"./agent/userdefine/")
        run("""
	   chmod a+x ./agent/userdefine/mongomon/bin/*
           sed -i 's:myip:%s:g' ./agent/userdefine/mongomon/bin/mongodb_monitor.py
           sed -i 's:myport:%s:g' ./agent/userdefine/mongomon/conf/mongomon.conf
           sed -i 's:myname:%s:g' ./agent/userdefine/mongomon/conf/mongomon.conf
           sed -i 's:mypass:%s:g' ./agent/userdefine/mongomon/conf/mongomon.conf
        """%(env.host,env.info['services']['mongo']['port'],env.info['services']['mongo']['usrname'],env.info['services']['mongo']['pwd']))
        sudo("""
           cd /etc/cron.d && sudo sed -i '/mongomon/g' machtalk
           cd /etc/cron.d && sudo echo '* * * * * machtalk source ~/.bashrc ;cd /opt/machtalk/agent/userdefine/mongomon/bin/ && ./mongomon_monitor.py >/dev/null' >> machtalk
        """)
        sudo("""
           easy_install pymongo
        """)


########## falcon deploy zk

@roles("zookeeper")
@task
def falcon_agent_plugin_zookeeper_deploy():
    with cd(env.remote_dir):
        put(env.local_softdir+"./agent.userdefine/zookeeper.check.sh", env.remote_dir+"./agent/userdefine/")
        run("""
	   chmod a+x ./agent/userdefine/zookeeper.check.sh
           sed -i 's:myport:%s:g' ./agent/userdefine/zookeeper.check.sh
           sed -i 's:myip:%s:g' ./agent/userdefine/zookeeper.check.sh
        """%(env.info['services']['zookeeper']['zkclientport'],env.host))
        sudo("""
           cd /etc/cron.d && sudo sed -i '/zookeeper/g' machtalk
           cd /etc/cron.d && sudo echo '* * * * * machtalk source ~/.bashrc ;cd /opt/machtalk/agent/userdefine/ && ./zookeeper.check.sh >/dev/null' >> machtalk
        """)
	# 把nc放过去	
        put(env.local_softdir+"others/nc", "/tmp/")
        sudo("""
		mv /tmp/nc /bin/
		chmod a+x /bin/nc
        """)

'''
伟大的注释

# 启动supervisor
supervisord -c /data/openfalcon/open-falcon/supervisor/supervisord.conf

# 清理没用的SQL信息
use dashboard;
delete from dashboard_graph;
delete from dashboard_screen;
delete from tmp_graph;

use graph
delete from endpoint;
delete from endpoint_counter;
delete from tag_endpoint;

use falcon_portal;
delete from grp;
delete from grp_host;
delete from grp_tpl;
delete from host;
delete from mockcfg;
delete from tpl;

userdefine.remotehttpcheck
userdefine.remotehttpcheck


each(metric=userdefine.remotehttpcheck)

# 定时语句
* * * * * cd /data/openfalcon/agent/userdefine && ./tcp.check 1>>/tmp/1.txt 2>&1
* * * * * cd /data/openfalcon/agent/userdefine && ./http.check 1>>/tmp/1.txt 2>&1

/data/openfalcon/open-falcon/agent/userdefine

/opt/machtalk/agent/userdefine


ip=127.0.0.1
to="wangyg@iiot.ac.cn"
subject="ceshi"
content="ceshi"
curl http://$ip:4000/sender/mail -d "tos=$to&subject=$subject&content=$content"
'''
