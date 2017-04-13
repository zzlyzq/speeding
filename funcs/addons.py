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

############# CONF yum From China
@task 
@roles('basic')
def yum_cn_conf():
    run("""

	sed -i '/proxy/d' /etc/yum.conf
	echo 'proxy=http://172.31.0.186:3128' >> /etc/yum.conf

	cd /etc/yum.repos.d/ && rm -f *


cat << 'EOF' > /etc/yum.repos.d/one.repo
[base]
name=CentOS-$releasever - Base - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/os/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/os/$basearch/
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=os
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-6

#released updates 
[updates]
name=CentOS-$releasever - Updates - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/updates/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/updates/$basearch/
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=updates
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-6

#additional packages that may be useful
[extras]
name=CentOS-$releasever - Extras - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/extras/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/extras/$basearch/
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=extras
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-6

#additional packages that extend functionality of existing packages
[centosplus]
name=CentOS-$releasever - Plus - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/centosplus/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/centosplus/$basearch/
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=centosplus
gpgcheck=1
enabled=0
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-6

#contrib - packages by Centos Users
[contrib]
name=CentOS-$releasever - Contrib - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/contrib/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/contrib/$basearch/
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=contrib
gpgcheck=1
enabled=0
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-6

[epel]
name=Extra Packages for Enterprise Linux 6 - $basearch
baseurl=http://mirrors.aliyun.com/epel/6/$basearch
        http://mirrors.aliyuncs.com/epel/6/$basearch
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-6&arch=$basearch
failovermethod=priority
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6

[epel-debuginfo]
name=Extra Packages for Enterprise Linux 6 - $basearch - Debug
baseurl=http://mirrors.aliyun.com/epel/6/$basearch/debug
        http://mirrors.aliyuncs.com/epel/6/$basearch/debug
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-debug-6&arch=$basearch
failovermethod=priority
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6
gpgcheck=0

[epel-source]
name=Extra Packages for Enterprise Linux 6 - $basearch - Source
baseurl=http://mirrors.aliyun.com/epel/6/SRPMS
        http://mirrors.aliyuncs.com/epel/6/SRPMS
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-source-6&arch=$basearch
failovermethod=priority
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6
gpgcheck=0
EOF
   """)

@task
@roles('basic')
def yum_us_conf():
    run("""
	sed -i '/proxy/d' /etc/yum.conf
	echo 'proxy=http://10.0.2.12:3128' >> /etc/yum.conf

	cd /etc/yum.repos.d/ && rm -f *
cat << 'EOF' > /etc/yum.repos.d/one.repo
[base]
name=CentOS-$releasever - Base
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=os&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/os/$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

#released updates 
[updates]
name=CentOS-$releasever - Updates
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=updates&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/updates/$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

#additional packages that may be useful
[extras]
name=CentOS-$releasever - Extras
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=extras&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/extras/$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

#additional packages that extend functionality of existing packages
[centosplus]
name=CentOS-$releasever - Plus
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=centosplus&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/centosplus/$basearch/
gpgcheck=1
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

#contrib - packages by Centos Users
[contrib]
name=CentOS-$releasever - Contrib
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=contrib&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/contrib/$basearch/
gpgcheck=1
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

[epel]
name=Extra Packages for Enterprise Linux 6 - $basearch
baseurl=http://mirror.rasanegar.com/fedoraproject/pub/epel/6/x86_64
failovermethod=priority
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6

[epel-debuginfo]
name=Extra Packages for Enterprise Linux 6 - $basearch - Debug
baseurl=http://mirror.rasanegar.com/fedoraproject/pub/epel/6/x86_64
failovermethod=priority
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6
gpgcheck=0

[epel-source]
name=Extra Packages for Enterprise Linux 6 - $basearch - Source
baseurl=http://mirror.rasanegar.com/fedoraproject/pub/epel/6/x86_64/
failovermethod=priority
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6
gpgcheck=0
EOF
""")

############# SQUID
@task
@roles('mgmt')
def squid_deploy():
    run("""
	yum install -y squid || echo "已经安装"
""")

    run("""
cat << 'EOF' > /etc/squid/squid.conf
http_port 0.0.0.0:3128
acl any src 10.0.0.0/8
http_access allow all
cache_mem 128 MB
maximum_object_size 4096 KB
maximum_object_size_in_memory 4096 KB
access_log /var/log/squid3/access.log squid
visible_hostname 10.0.0.2
cache_dir ufs /var/spool/squid3 1000 16 256
cache_mgr XXX
EOF

mkdir -p /var/spool/squid3
chown squid:squid /var/spool/squid3
chmod 777 /var/spool/squid3

mkdir -p /var/log/squid3
chown squid:squid /var/log/squid
squid -z
#service squid restart
squid
""")


############# PROXYCHAINS
@task
@roles('proxychains')
def proxychains_putfile():
    put(env.local_softdir+"proxychains.tar.gz",env.remote_dir)

@task
@roles('proxychains')
def proxychains_deploy():
    with cd(env.remote_dir):
        run("""
        tar xzvf proxychains.tar.gz
        cp -f ./proxychains/proxychains.conf /etc/
        cp -f ./proxychains/libproxychains4.so /usr/local/lib/
        cp -f ./proxychains/proxychains4 /bin/
        """)
        run("""
cat << 'EOF' > /etc/proxychains.conf
proxy_dns
tcp_read_time_out 5000
tcp_connect_time_out 5000
localnet 10.0.0.0/255.0.0.0
localnet 192.168.0.0/255.255.0.0
localnet 172.16.16.0/255.240.0.0
[ProxyList]
socks5	1.1.1.67 1180
EOF""")

############# PXE
@task
@roles("pxe")
def pxe_putfile():
    # for dnsmasq
    put(env.local_softdir+"dnsmasq.tar.gz", env.remote_dir)
    put(env.local_softdir+"lighttpd.tar.gz", env.remote_dir)
    # for

@task
@roles("pxe")
def pxe_deploy():
    with cd(env.remote_dir):
	run("""
        # 解压数据
        tar xzf dnsmasq.tar.gz
        tar xzf lighttpd.tar.gz
	""")

        # conf for dnsmasq
        run("""
cat << 'EOf' >> ./dnsmasq/tftpboot/pxelinux.cfg
default 1
prompt 10
timeout 600

#label 0
#  localboot 0xffff

label 1
  kernel kernel/vmlinuz
  ipappend 2
  append initrd=image/initrd.img ks=http://192.168.9.1/ks.cfg ip=dhcp ksdevice=bootif
EOF""")

@task
@roles("pxe")
def pxe_restart():
    with cd(env.remote_dir):
    # start for dnsmasq
        run("""
    cd dnsmasq && ./start.sh
    cd ..
    cd lighttpd && ./restart
    """)
############# PHPREDIS
@task
@roles("")
def phpredis_putfile():
    put(env.local_softdir+"phpredis.tar.gz",env.remote_dir)

@task
@roles("")
def phpredis_deploy():
    with cd(env.remote_dir):
        run("tar xzf phpredis.tar.gz")
        run("""
            cd phpredis
        """)

@task
@roles("")
def phpredis_restart():
    with cd(env.remote_dir):
        run("""
        cd phpredis
        restart
        """)
