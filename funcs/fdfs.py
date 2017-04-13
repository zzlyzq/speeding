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

############# FDFS START

def getConfigForStorage(ip, storages,trackers):
    # 找到我的group_name
    myGroupName = ""
    i = 1
    for storage in storages:
        print storage
        if ip in storage:
            print "ip belong to group %s"%i
            myGroupName = "group%s"%i
        i += 1
    # trackers 本身就是tracker的列表
    # 生成storage配置
    conf_storage_part1 = """
disabled=false
bind_addr=
client_bind=true
connect_timeout=30
network_timeout=60
heart_beat_interval=30
stat_report_interval=60
max_connections=100000
buff_size = 256KB
accept_threads=1
work_threads=4
disk_rw_separated = true
disk_reader_threads = 1
disk_writer_threads = 1
sync_wait_msec=50
sync_interval=0
sync_start_time=00:00
sync_end_time=23:59
write_mark_file_freq=500
subdir_count_per_path=256
log_level=info
run_by_group=
run_by_user=
allow_hosts=*
file_distribute_path_mode=0
file_distribute_rotate_count=100
fsync_after_written_bytes=0
sync_log_buff_interval=10
sync_binlog_buff_interval=10
sync_stat_file_interval=300
thread_stack_size=512KB
upload_priority=10
if_alias_prefix=
check_file_duplicate=0
file_signature_method=hash
key_namespace=FastDFS
keep_alive=0
use_access_log = false
rotate_access_log = false
access_log_rotate_time=00:00
rotate_error_log = false
error_log_rotate_time=00:00
rotate_access_log_size = 0
rotate_error_log_size = 0
log_file_keep_days = 0
file_sync_skip_invalid_record=false
use_connection_pool = false
connection_pool_max_idle_time = 3600
http.domain_name=
http.server_port=8888
            """
    conf_storage_part2="""
port=23000
store_path_count=1
base_path=/opt/machtalk/fastdfs/data/fastdfs_storage
group_name=%s
    """%(myGroupName)
    conf_storage_part3=""
    for tracker in trackers:
        #print tracker
        conf_storage_part3 += "tracker_server=%s:22122\n"%(tracker)
    #print conf_storage_part3
    conf_storage = """
%s
%s
%s
    """%(conf_storage_part1,conf_storage_part2,conf_storage_part3)
    return conf_storage
def getConfigForTracker():
    conf_tracker = """
disabled=false
bind_addr=
connect_timeout=30
network_timeout=60
max_connections=100000
accept_threads=1
work_threads=4
store_server=0
store_path=0
download_server=0
reserved_storage_space = 10%
log_level=debug
allow_hosts=*
sync_log_buff_interval = 10
check_active_interval = 120
thread_stack_size = 64KB
storage_ip_changed_auto_adjust = true
storage_sync_file_max_delay = 86400
storage_sync_file_max_time = 300
use_trunk_file = false
slot_min_size = 256
slot_max_size = 16MB
trunk_file_size = 64MB
trunk_create_file_advance = false
trunk_create_file_time_base = 02:00
trunk_create_file_interval = 86400
trunk_create_file_space_threshold = 20G
trunk_init_check_occupying = false
trunk_init_reload_from_binlog = false
trunk_compress_binlog_min_interval = 0
use_storage_id = false
storage_ids_filename = storage_ids.conf
id_type_in_filename = ip
store_slave_file_use_link = false
rotate_error_log = false
error_log_rotate_time=00:00
rotate_error_log_size = 0
log_file_keep_days = 0
use_connection_pool = false
connection_pool_max_idle_time = 3600
http.server_port=8080
http.check_alive_interval=30
http.check_alive_type=tcp
http.check_alive_uri=/status.html
run_by_group=machtalk
run_by_user=machtalk
store_lookup=2
port=22122
base_path=/opt/machtalk/fastdfs/data/fastdfs_tracker/
    """
    return conf_tracker
def getConfigForModFastDFS(ip, storages, trackers):
    # 找到我的group_name
    myGroupName = ""
    i = 1
    for storage in storages:
        print storage
        if ip in storage:
            print "ip belong to group %s"%i
            myGroupName = "group%s"%i
        i += 1

    conf = ""

    conf += '''
connect_timeout=2
network_timeout=30
base_path=/opt/machtalk/fastdfs/data/fastdfs_storage
load_fdfs_parameters_from_tracker=true
storage_sync_file_max_delay = 86400
use_storage_id = false
storage_ids_filename = storage_ids.conf
url_have_group_name = true
store_path_count=1
store_path0=/opt/machtalk/fastdfs/data/fastdfs_storage
log_level=info
log_filename=
response_mode=proxy
if_alias_prefix=
flv_support = true
flv_extension = flv
group_count = 0
'''

    conf += '''
storage_server_port=%s:23000
''' % ip

    conf += '''
group_name=%s
'''%myGroupName

    for tracker in trackers:
        conf += '''
tracker_server=%s:22122
'''%(tracker)

    conf += '''#include http.conf'''


    return conf
def getConfigForStorageNginx(ip, storages):
    # 找到我的group_name
    myGroupName = ""
    i = 1
    for storage in storages:
        print storage
        if ip in storage:
            print "ip belong to group %s"%i
            myGroupName = "group%s"%i
        i += 1
    # 生成配置
    conf_nginx = """
server {

    listen 8088;
    server_name uploadserver,_;

    access_log /opt/machtalk/nginx/logs/a.8088.log;
    error_log /opt/machtalk/nginx/logs/e.8088.log;

    location /%s/M00 {
        root /opt/machtalk/fastdfs/data/fastdfs_storage/data;
        ngx_fastdfs_module;
    }

}
            """%(myGroupName)
    return conf_nginx
def getConfigForNginx(ip,storages):
    # 找到我的group_name
    myGroupName = ""
    myGroupNumber = int
    groupTotal = len(storages)
    i = 1
    for storage in storages:
        print storage
        if ip in storage:
            print "ip belong to group %s"%i
            myGroupNumber = i
            myGroupName = "group%s"%i
        i += 1
    conf_nginx = ""

    for x in range(1,groupTotal+1):
        conf_nginx += """
upstream fdfs_group%s {
"""%(x)
        for value in storages[x - 1]:
            conf_nginx += """
    server %s:8088 weight=1 max_fails=2 fail_timeout=30s;
"""%value
        conf_nginx += """
}
"""

    conf_nginx += """
proxy_cache_path /opt/machtalk/nginx/http-cache levels=1:2 keys_zone=http-cache:20m inactive=1d max_size=100m;
"""
    conf_nginx += """
server {
    listen       8090;
    server_name  localhost,_;

    access_log /opt/machtalk/nginx/logs/a.8090.log;
    error_log /opt/machtalk/nginx/logs/e.8090.log;
"""
    for x in range(1,groupTotal+1):
        conf_nginx += """
    location /group%s/M00 {
        proxy_next_upstream http_502 http_504 error timeout invalid_header;
        proxy_cache http-cache;
        proxy_cache_valid  200 304 12h;
        proxy_cache_key $uri$is_args$args;
        proxy_pass http://fdfs_group%s;
        expires 30d;
    }
"""%(x,x)

    conf_nginx += """
}
    """

    return conf_nginx
def getConfigForClient(trackers):
    conf_client = ""
    conf_client += """
connect_timeout=30
network_timeout=60
base_path=/opt/machtalk/fastdfs/data/fastdfs_storage
log_level=info
use_connection_pool = false
connection_pool_max_idle_time = 3600
load_fdfs_parameters_from_tracker=false
use_storage_id = false
storage_ids_filename = storage_ids.conf
http.tracker_server_port=80
    """

    for tracker in trackers:
        conf_client +="""
tracker_server=%s:22122
        """%tracker

    return conf_client

@roles('fdfs')
@task
def fdfs_deploy():
  info = env.info
  with cd(env.remote_dir):
      # 变量
      ip = env.host

      # 开始部署
      run("echo 'start deploy fdfs'")

      # 异常停止，如果存在fastdfs文件夹，就退出
      #run("""[ -e "./fastdfs" ] && exit 1 || echo '开始部署fastdfs！'""")

      ifExists=run(""" [ -e "./fastdfs" ] && echo "cunzai" || echo 'bucunzai'""")
      # 上传文件
      if ifExists == "bucunzai":
          put(env.local_softdir + "fastdfs.tar.gz", env.remote_dir)
          put(env.local_softdir + "nginx.tar.gz", env.remote_dir)
          put(env.local_softdir + "addons.tar.gz", env.remote_dir)
          run("""
          tar xzf ./fastdfs.tar.gz
          tar xzf ./nginx.tar.gz
          tar xzf ./addons.tar.gz
          rm -f ./fastdfs.tar.gz
          rm -f ./nginx.tar.gz
          rm -f ./addons.tar.gz
          """)
          run("ln -s %s/fastdfs/data/fastdfs_storage/data %s/fastdfs/data/fastdfs_storage/data/M00"%(env.remote_dir,env.remote_dir))

          # 权限修改
          run("chown -R machtalk:machtalk fastdfs addons nginx")
      else:
          print "目录已经存在,我们只是修改配置文件!"

      # 环境变量写入
      #run('echo "' + ip + ' tracker1" >> /etc/hosts')
      run(" sed -i '/libfastcommon/d' ~/.bashrc  ")
      run(" sed -i '/fastdfs/d' ~/.bashrc  ")
      run("sed -i '$a export LD_LIBRARY_PATH=" + env.remote_dir + "addons/libfastcommon/lib:$LD_LIBRARY_PATH' " + env.remote_dir + ".bashrc")
      run("sed -i '$a export LD_LIBRARY_PATH=" + env.remote_dir + "fastdfs/usr/lib64/:$LD_LIBRARY_PATH' " + env.remote_dir + ".bashrc")
      run("sed -i '$a export PATH=" + env.remote_dir + "fastdfs/usr/bin:$PATH' " + env.remote_dir + ".bashrc")
      run("sed -i '$a export PATH=" + env.remote_dir + "nginx/sbin:$PATH' " + env.remote_dir + ".bashrc")
      run("chmod 755 ./fastdfs/etc/init.d/*")
      run("chmod 755 ./fastdfs/usr/bin/*")
      run("chmod 755 ./nginx/sbin/*")
      run("chmod 755 ./nginx/bin/nginx")

      # 清除老的nginx配置
      run("rm -f ./nginx/conf/servers/*.conf")

      # 判断是否是storage
      print "判断是否是storage角色"
      print info['services']['fdfs']['storages']
      print type(info['services']['fdfs']['storages'])
      for storage in info['services']['fdfs']['storages']:
          print "storage的值是：",
          print storage
          #print storage
          print "env.host的值是 %s"%env.host
          print "ip的值是%s"%ip
          if env.host in storage:
              print "当前主机是storage，需要实行两个函数。"
              confForStorage = getConfigForStorage(env.host, info['services']['fdfs']['storages'], info['services']['fdfs']['trackers'])
              run(""" echo '%s' > /opt/machtalk/fastdfs/etc/fdfs/storage.conf"""%confForStorage)
              run(""" set -m ; /opt/machtalk/fastdfs/etc/init.d/fdfs_storaged restart""")
              confForModFastDFS = getConfigForModFastDFS(env.host, info['services']['fdfs']['storages'], info['services']['fdfs']['trackers'])
              run(""" echo '%s' > /opt/machtalk/fastdfs/etc/fdfs/mod_fastdfs.conf"""%confForModFastDFS)
              confForStorageNginx = getConfigForStorageNginx(env.host, info['services']['fdfs']['storages'])
              run(""" echo '%s' > /opt/machtalk/nginx/conf/servers/storage.conf""" % confForStorageNginx)
              #run(""" kill -9 `cat /opt/machtalk/nginx/logs/nginx.pid` && echo '停止nginx成功!' || echo '停止nginx异常!'""")
              run("""
                  while [ $(ps aux | grep nginx | grep -v grep | wc -l) -gt 0 ]
                  do
                      ps aux | grep nginx | grep -v grep | awk '{print $2}' | xargs -i kill -9 {}
                  done
              """)
              run(""" set -m ; /opt/machtalk/nginx/sbin/nginx""")

      # 判断是否是tracker
      print "判断是否是Tracker角色"
      if ip in info['services']['fdfs']['trackers']:
          confForTracker = getConfigForTracker()
          run(""" echo '%s' > /opt/machtalk/fastdfs/etc/fdfs/tracker.conf""" % confForTracker)
          run(""" set -m ; /opt/machtalk/fastdfs/etc/init.d/fdfs_trackerd restart""")

      # 判断是否是nginx
      print "判断是否是nginx角色"
      if ip in info['services']['fdfs']['nginxs']:
          confForNginx = getConfigForNginx(env.host,info['services']['fdfs']['storages'])
          run(""" echo '%s' > /opt/machtalk/nginx/conf/servers/nginx.conf""" % confForNginx)
          run("""
              while [ $(ps aux | grep nginx | grep -v grep | wc -l) -gt 0 ]
              do
                  ps aux | grep nginx | grep -v grep | awk '{print $2}' | xargs -i kill -9 {}
              done
          """)
          run(""" set -m ; /opt/machtalk/nginx/sbin/nginx""")

      # 不管是nginx还是storage还是tracker,都部署client配置
      if 1 == 1:
          confForClient = getConfigForClient(info['services']['fdfs']['trackers'])
          run(""" echo '%s' > /opt/machtalk/fastdfs/etc/fdfs/client.conf"""%confForClient)

@task
@roles("fdfs")
def fdfs_restart():
    with cd(env.remote_dir):
        run("""
           ~/fastdfs/etc/init.d/fdfs_trackerd start
           ~/fastdfs/etc/init.d/fdfs_storaged start
           ~/nginx/bin/nginx restart
        """)

'''
  # 下面为备注,有些命令用于测试

  # fastdfs测试
  dd if=/dev/zero of=10mb.png bs=1M count=10
  /opt/machtalk/fastdfs/usr/bin/fdfs_upload_file /opt/machtalk/fastdfs/etc/fdfs/client.conf 10mb.png && echo "OK" || echo "Error"
  /opt/machtalk/fastdfs/usr/bin/fdfs_download_file /opt/machtalk/fastdfs/etc/fdfs/client.conf  group1/M00/00/01/wKgDhVgywL6ADwEkAKAAAHBWCyc529.png
  wget http://127.0.0.1:8090/group1/M00/00/01/wKgDhVir_ZeABF_TAKAAAHBWCyc486.png

  # fastdfs 重启
    /opt/machtalk/fastdfs/etc/init.d/fdfs_trackerd restart
    /opt/machtalk/fastdfs/etc/init.d/fdfs_storaged restart

  # fastdfs 日志查看
    tail -fn 40 /opt/machtalk/fastdfs/data/fastdfs_tracker/logs/trackerd.log

    tail -fn 40 /opt/machtalk/fastdfs/data/fastdfs_storage/logs/storaged.log

  # fastdfs 停止
  /opt/machtalk/fastdfs/etc/init.d/fdfs_trackerd stop
  /opt/machtalk/fastdfs/etc/init.d/fdfs_storaged stop
  killall nginx


  #fastdfs 启动
  ./fastdfs/etc/init.d/fdfs_trackerd start
  ./fastdfs/etc/init.d/fdfs_storaged start
  killall nginx

   # TODO 启动和检查需要跟进
'''
