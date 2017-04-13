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

############## CDH

@task
@roles("cdh")
def cdh_pufile():
    # 上传文件
    run("mkdir -p /opt/cloudera/parcel-repo/")
    run("mkdir -p /opt/cdh-cm/share/cmf/lib/")
    put(env.local_softdir + "cloudera-manager-el6-cm5.5.0_x86_64.tar.gz", "/opt/")
    put(env.local_softdir + "solrcloud.tar.gz", "/opt/")
    put(env.local_softdir + "CDH-5.5.0-1.cdh5.5.0.p0.8-el6.parcel", "/opt/cloudera/parcel-repo/")
    put(env.local_softdir + "CDH-5.5.0-1.cdh5.5.0.p0.8-el6.parcel.sha", "/opt/cloudera/parcel-repo/")
    put(env.local_softdir + "manifest.json", "/opt/cloudera/parcel-repo/")
    put(env.local_softdir + "mysql-connector-java-5.1.38-bin.jar", "/opt/cdh-cm/share/cmf/lib/")

@task
@roles("cdh")
def cdh_deploy():
    with cd("/opt/"):
        # 判断目录是否存在，如果存在就退出
        run(""" [ -e "/opt/cm" ] && exit 1 || echo '开始部署CDH！' """)

        # 根据变量获取
        ip = env.host
        ipListNumber = json.loads(bo.servers).index(ip) + 1
        serverName = "cdhslave%s" % (ipListNumber)
        if ipListNumber == 1:
            serverName = "cdhmanager"

        # 设置主机名
        sudo("""
    cat << 'EOF' > /etc/sysconfig/network
    NETWORKING=yes
    HOSTNAME=%s
    EOF
    hostname %s
                    """ % (serverName, serverName))

        # 设置hosts
        conf_hosts = ""
        itemNumber = 0
        for item in json.loads(bo.servers):
            if itemNumber == 0:
                conf_hosts += """
    %s cdhmanager""" % (item)
            else:
                conf_hosts += """
    %s cdhslave%s""" % (item, itemNumber + 1)
            itemNumber += 1
        sudo("""
                        sed -i "/cdhslave/d" /etc/hosts
                        sed -i "/cdhmanager/d" /etc/hosts
                        service network restart
                        echo '%s' >> /etc/hosts
                    """ % (conf_hosts))

        # 上传文件
        # put(Const.SOURCE_DIR + "cloudera-manager-el6-cm5.5.0_x86_64.tar.gz", "/opt/")
        run("tar -xzf /opt/cloudera-manager-el6-cm5.5.0_x86_64.tar.gz -C /opt/")
        run("ln -s /opt/cm-5.5.0 /opt/cdh-cm")
        # put(Const.SOURCE_DIR + "solrcloud.tar.gz", "/opt/")
        run("tar -xzf ./solrcloud.tar.gz")
        # put(Const.SOURCE_DIR + "CDH-5.5.0-1.cdh5.5.0.p0.8-el6.parcel", "/opt/cloudera/parcel-repo/")
        #put(Const.SOURCE_DIR + "CDH-5.5.0-1.cdh5.5.0.p0.8-el6.parcel.sha", "/opt/cloudera/parcel-repo/")
        #put(Const.SOURCE_DIR + "manifest.json", "/opt/cloudera/parcel-repo/")
        #put(Const.SOURCE_DIR + "mysql-connector-java-5.1.38-bin.jar", "/opt/cdh-cm/share/cmf/lib/")

        # 修改主机名 为 cdhmanassger
        run("""
        hostname cdhmanager
        sed -i 's/HOSTNAME=.*/HOSTNAME=cdhmanager/g' /etc/sysconfig/network
        sed -i '/cdhmanager/d' /etc/hosts
        echo "%s  cdhmanager" >> /etc/hosts
        service network restart
        """%env.host)


        # 添加cloudera-scm账户
        run("useradd --system --home=/opt/cdh-cm/run/cloudera-scm-server/ --no-create-home --shell=/bin/false --comment 'Cloudera SCM User' cloudera-scm | echo 'account alreay exists'")

        # cdhmanager服务器ssh key
        run('''
            ssh-keygen -t rsa -C 'cdh' -P '' -f  ~/.ssh/id_rsa
            cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
            chmod 600 ~/.ssh/authorized_keys
            ''')

        # 只有cdhamnager需要执行下面的命令
        if serverName == "cdhmanager":
            # 配置修改
            ## agent
            run(
                "sed -i 's/server_host=localhost/server_host=cdhmanager/g' /opt/cdh-cm/etc/cloudera-scm-agent/config.ini")
            # 数据库配置
            conf_cdhserver = """
    com.cloudera.cmf.db.type=mysql
    com.cloudera.cmf.db.host=%s
    com.cloudera.cmf.db.name=%s
    com.cloudera.cmf.db.user=%s
    com.cloudera.cmf.db.password=%s
                """ % (info['services']['cdh']['dbip'], "cm", "scm", "scm")
            run(""" echo '%s' > /opt/cm-5.5.0/etc/cloudera-scm-server/db.properties """ % conf_cdhserver)

            # 数据库建库
            # 需要变量dbip dbname dbpass
            ## 确保mysql客户端存在
            run(""" yum install -y mysql || echo 'mysql客户端已经安装!'""")
            ## for database amon
            run(
                """ mysql -h %s -u%s -p%s -e "create database amon DEFAULT CHARSET utf8 COLLATE utf8_general_ci;" """ % (
                info['services']['cdh']['dbip'], info['services']['cdh']['dbusrname'], info['services']['cdh']['dbpwd']))
            run(
                """ mysql -h %s -u%s -p%s -e "grant all privileges on amon.* to 'amon'@'%s' identified by 'amon'; flush privileges;" """ % (
                    info['services']['cdh']['dbip'], info['services']['cdh']['dbusrname'],
                    info['services']['cdh']['dbpwd'], "%"))
            run(
                """ mysql -h %s -u%s -p%s -e "grant all privileges on amon.* to 'amon'@'%s' identified by 'amon'; flush privileges;" """ % (
                    info['services']['cdh']['dbip'], info['services']['cdh']['dbusrname'],
                    info['services']['cdh']['dbpwd'], "localhost"))
            ##  for database cm
            run(""" mysql -h %s -u%s -p%s -e "create database cm DEFAULT CHARSET utf8 COLLATE utf8_general_ci;" """ % (
                info['services']['cdh']['dbip'], info['services']['cdh']['dbusrname'], info['services']['cdh']['dbpwd']))
            run(
                """ mysql -h %s -u%s -p%s -e "grant all privileges on cm.* to 'scm'@'%s' identified by 'scm'; flush privileges;" """ % (
                    info['services']['cdh']['dbip'], info['services']['cdh']['dbusrname'],
                    info['services']['cdh']['dbpwd'], "%"))
            run(
                """ mysql -h %s -u%s -p%s -e "grant all privileges on cm.* to 'scm'@'%s' identified by 'scm'; flush privileges;" """ % (
                    info['services']['cdh']['dbip'], info['services']['cdh']['dbusrname'],
                    info['services']['cdh']['dbpwd'], "localhost"))

            # 数据库初始化
            run('/opt/cdh-cm/share/cmf/schema/scm_prepare_database.sh mysql cm --scm-host ' + ip + ' scm scm scm')

            # 启动server
            run("/opt/cdh-cm/etc/init.d/cloudera-scm-server start")

        # 启动agent
        run("""
                sed -i 's:server_host=.*:server_host=cdhmanager:g' /opt/cm-5.5.0/etc/cloudera-scm-agent/config.ini
                /opt/cm-5.5.0/etc/init.d/cloudera-scm-agent restart
            """)

    ''' 伟大的注释
    # cdh - 3 - 数据库初始化
    @task
    @roles('cdh')
    def cdh3():
      ip = run("/sbin/ifconfig | grep '10\.\|192\.168\.' | head -n 1 | awk -F\: '{print $2}' | awk '{print $1}'")
      dbip=ip
      # for database amon
      run(""" mysql -e "create database amon DEFAULT CHARSET utf8 COLLATE utf8_general_ci;" """)
      run(""" mysql -e "grant all privileges on amon.* to 'amon'@'%s' identified by 'amon'; flush privileges;" """%("%"))
      run(""" mysql -e "grant all privileges on amon.* to 'amon'@'%s' identified by 'amon'; flush privileges;" """%("localhost"))
      #A for database cm
      run(""" mysql -e "create database cm DEFAULT CHARSET utf8 COLLATE utf8_general_ci;" """)
      run(""" mysql -e "grant all privileges on cm.* to 'scm'@'%s' identified by 'scm'; flush privileges;" """%("%"))
      run(""" mysql -e "grant all privileges on cm.* to 'scm'@'%s' identified by 'scm'; flush privileges;" """%("localhost"))
      # for database hive
      #run(""" mysql -e "create database hive DEFAULT CHARSET utf8 COLLATE utf8_general_ci;" """)
      #run(""" mysql -e "grant all privileges on hive.* to 'hive'@'%s' identified by 'hive'; flush privileges;" """%("%"))
      #run(""" mysql -e "grant all privileges on hive.* to 'hive'@'%s' identified by 'hive'; flush privileges;" """%("localhost"))
      # for database hue
      #run(""" mysql -e "create database hue DEFAULT CHARSET utf8 COLLATE utf8_general_ci;" """)
      #run(""" mysql -e "grant all privileges on hue.* to 'hue'@'%s' identified by 'hue'; flush privileges;" """%("%"))
      #run(""" mysql -e "grant all privileges on hue.* to 'hue'@'%s' identified by 'hue'; flush privileges;" """%("localhost"))
      # for a special user
      #run(""" mysql -e "grant all privileges on *.* to 'machtalk'@'%s' identified by 'machmydb'; flush privileges;" """%("%"))
      #run(""" mysql -e "grant all privileges on *.* to 'machtalk'@'%s' identified by 'machmydb'; flush privileges;" """%("localhost"))
      #run(""" mysql -e "grant all privileges on *.* to 'machtalk'@'%s' identified by 'machmydb'; flush privileges;" """%("cdhmanager"))
      #scm back is clouder_manager_server ip
      run('/opt/cdh-cm/share/cmf/schema/scm_prepare_database.sh mysql cm --scm-host '+ip+' scm scm scm')

    # cdh - 4 - 启动服务
    @task
    @roles('cdh')
    def cdh4():
      run("/opt/cdh-cm/etc/init.d/cloudera-scm-server start")
      run("/opt/cdh-cm/etc/init.d/cloudera-scm-agent start")
    '''

    '''
    清空当前cloudera
    cd /opt ; rm -rf cloud*
    cd /opt ; rm -rf cm*
    cd /opt ; rm -rf solr*
    cd /opt ; rm -rf cdh-cm
    '''

    ''' 最后配置
    su hdfs
    hadoop fs -setrep 2 /

    '''

@task
@roles("cdh")
def cdh_clean():
    pass