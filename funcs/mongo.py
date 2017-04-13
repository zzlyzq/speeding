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

############## MONGO

def getConfigForHosts(servers):
    i = 1
    result = ""
    for ip in servers[3]:
        value1 = ip
        value2 = "mongo%s" % i
        result += """
%s %s""" % (value1, value2)

        i += 1
    return result
def getConfigForConfig():
    conf = ""
    conf += "/opt/machtalk/mongo/bin/mongod --configsvr --dbpath /opt/machtalk/mongo/config/data --port 21000 --logpath /opt/machtalk/mongo/config/log/config.log --fork"
    return conf
def getConfigForMongos(servers):
    cmdMongos = ""
    cmdMongos += """/opt/machtalk/mongo/bin/mongos  --configdb """
    aList = []
    for ip in servers[0]:
        number = servers[3].index(ip)
        aList.append("mongo%s:21000" % str(int(number) + 1))
    cmdMongos += ','.join(aList)
    cmdMongos += """ --port 20000 --logpath /opt/machtalk/mongo/mongos/log/mongos.log --fork"""
    return cmdMongos

@task
@roles('mongo')
def mongo_deploy():
    with cd(env.remote_dir):
        # 获取fabric传过来的变量
        ip = env.host
        info = env.info
        # 判断， 文件是否存在
        # tarFileName = "./mongodb-linux-x86_64-2.6.11.tar.gz"
        #if run("[ -e '%s' ] "%tarFileName):
        #    print "文件存在！"
        #else:
        #    print "文件不存在！"
        #return 1
        #if run("[ -e '%s' ] " % tarFileName) == 0:
        #    print "文件已经存在!"
        #else:
        #    print "文件不存在！"
        #return 1
        # 判断目录是否存在，如果存在就退出,返回0代表错误
        #run(''' [ -e "./mongo" ] && exit 0 || echo '开始部署mongo！' ''')

        # 上传文件
        # put("%smongodb-linux-x86_64-2.6.11"%Const.SOURCE_DIR,Const.DEST_DIR)
        fileNeedTransfer = []
        fileNeedTransfer.append("mongodb-linux-x86_64-2.6.11.tar.gz")
        for tarFileName in fileNeedTransfer:
            #if run("[ -e $tarFileName ] && exit 0 || exit 1"):
            put("%s%s" % (env.local_softdir,tarFileName), env.remote_dir)
            run("tar xzf %s" % tarFileName)
            #run("rm -f %s" % tarFileName)

        # 做软链
        run('''ln -s ./mongodb-linux-x86_64-2.6.11 ./mongo && echo '软链创建成功！' || echo '软链已经存在！' ''')

        # 补充一个keyFile
        keyFile = """uWlQGXp+hJtGp0+xphUZ0Lmit+6bp3xW0+HprUE6qx4YHcJ2DjDnZa9SgUxbukhB
Xi+wDVDNMp1RYOuvkc+5C+3fhkeqrNKXbXvegQC7a4zDKjgjXR2BbdHxVyakg3sf
Jjve561yI8ayP5o/R1euHOTNxWwUjQBTOQ/pGU2Ju01jsd7BbX9hhTCePP6Uj7dN
CJROyc/NylR18lN2VGkT2pWagxfbJc7oMGW7smHlLvnONVuw5i4YUcIafjcFfZjs
EMfJbhpcMSMrmEW+dfeBXdXYhhGEt4arDgaeqJFTbIx08UTKXb7yDl7zppMaHLn9
zidhjlnx21Qj/I6G7PMm/7odScr2ksE8ut6WAdxnsCnmGKEc4QcrgonxHZtwMltm
F1ZWUM3M6As7MGZK7yVr8bY/0EQRZyqXYmGr5b5UPsA95eTHV3kGbSdZu/r53G7r
jxjV2sEfinsqahRG0jd1yLC32R4RJLQ4XluYfI0AnDncgY9POdMOjClx4unip0K0
db3pwvSi2pTpva6IOLiiCnYYjTAIOeqUMj5LIr+I57r97t8EKdBRtVlh6tJtk5AL
XALg74JNHwuTCZhGaGMlu1n4wE4rSPbid0Wn/+cMhJxg91wgaE8IMECI8lAF2mMV
0cNE+74nbjo0Zyt0tGJYf4vBZqNvi02XGLPXns1KdCmnfwm6AVuNZ4SIZMLyPMG7
wmEqGHCgKFZOBfm+LL3WOPMg8YVbw496RbkymOib8SIrzyX2y2bUDf3YMU/iHr7z
vSQeIrkAhiutxp2FuNMm1nw2Y+lQqcTlRcRr3KdkvsbRQsqAlsbGqwTJCg8+y7AC
WMla/EMXtYXW0bjGYKteck/uIYxANRsmJ9BA34ua507+wm8sWRR8LswaVlkdAmUv
HrYBkulehOcxAyInWgBOwIrf+Te+5hAqJw3ZEbxBxcsyi7PA5YBmhMCCPdlbaBQE
INWjELDdgIQ3hHTM/yNofkqWK7Pc2msUr4zodssMn3oZ"""
        run(""" echo '%s' > ./mongo/keyfile""" % keyFile)
        run("chmod 600 ./mongo/keyfile")

        # 写一个重启脚本到boot目录
        run("""
mkdir -p ./mongo/boot
cat << 'EOF' > ./mongo/boot/restart
#!/bin/bash

# 杀掉所有mongo相关进程
ps aux | grep log | grep mongo | grep -v grep | awk '{print $2}' | xargs -i kill -9 {}
find ~ -name *.lock | xargs -i rm -f {}

# 进入到目录
cd /opt/machtalk/mongo/boot

# 修改所有服务,如果没有keyFile那么就添加

# 重新启用所有脚本
for i in `ls *.sh`
do
    echo "正在处理$i文件"
    ifHaveKeyFile=`cat $i | grep "keyFile" | wc -l`
    if [ $ifHaveKeyFile -eq 0 ];
    then
        echo "文件需要添加keyFile指令, 需要修改!"
        sed -i '1 s:$: --keyFile /opt/machtalk/mongo/keyfile:g' ./$i
    else
        echo "文件已经有keyfile指令了, 无需修改!"
    fi
    echo "正在启动服务$i"
    ./$i
done
EOF
""")
        run(""" chmod a+x ./mongo/boot/restart """)

        # 修改环境变量
        run('''
        sed -i '/mongo/d' ~/.bashrc
        sed -i '$a export PATH=%s/mongo/bin:$PATH' ~/.bashrc
        ''' % (env.remote_dir))

        # 修改权限
        run("chmod 755 ./mongo/bin/*")
        run("chmod 755 ./mongo/my_mongo")

        # 开始配置
        # 设置hosts, 每台机器都要知道所有mongo 列表的hosts对应,获取方式就是bo.servers最后一个列表
        sudo('''
            cp -f /etc/hosts /etc/hosts.bak
            sed -i "/mongo/d" /etc/hosts
            echo '%s' >> /etc/hosts
        ''' % (getConfigForHosts(info['services']['mongo']['servers'])))

        # 相关
        run('''
            mkdir -p ./mongo/boot/
        ''')

        # 判断如果是config server
        if ip in info['services']['mongo']['servers'][0]:
            print "I am running as a config server!"
            run('''
                mkdir -p ./mongo/config/{data,log} || echo "目录已经存在!"
                echo '%s' > ./mongo/boot/config.sh
                chmod a+x ./mongo/boot/config.sh
                ./mongo/boot/config.sh
            ''' % getConfigForConfig())

        # 判断您是否是mongos server
        if ip in info['services']['mongo']['servers'][1]:
            print "I am running as a mongos server!"
            run('''
                mkdir -p ./mongo/mongos/log || echo "目录已经存在!"
            ''')
            run('''
                echo '%s' > ./mongo/boot/mongos.sh
                chmod a+x ./mongo/boot/mongos.sh
                #./mongo/boot/mongos.sh
            ''' % (getConfigForMongos(info['services']['mongo']['servers'])))

        # 判断是否是shard server
        if ip in info['services']['mongo']['servers'][2]:
            print "I am running as a shard server!"
            print info['services']['mongo']['shardtotal']
            for i in range(1, int(info['services']['mongo']['shardtotal']) + 1):
                run('''
                    mkdir -p ./mongo/shard%s/{data,log} || echo "目录已经存在!"
                    echo '/opt/machtalk/mongo/bin/mongod --shardsvr --replSet shard%s --port 2200%s --dbpath /opt/machtalk/mongo/shard%s/data  --logpath /opt/machtalk/mongo/shard%s/log/shard%s.log --fork --nojournal  --oplogSize 10' > ./mongo/boot/shard%i.sh
                    chmod a+x ./mongo/boot/shard%s.sh
                    # 时间不同步,会造成卡住不动
                    ./mongo/boot/shard%s.sh
                    ''' % (i, i, i, i, i, i, i, i, i))

        # 服务停止与启动
        # run("./mongo/my_mongo stop || echo '服务已经停止！' ")
        # run("./mongo/my_mongo start || echo '服务启动异常！' ")
        # """
        # 在最后一台机器上执行
        if ip == info['services']['mongo']['servers'][3][-1]:
            # 执行mongos
            run("./mongo/boot/mongos.sh")
            # mongo 集群 配置配置
            ## 配置shard1 replica-set
            run(
                ''' ./mongo/bin/mongo mongo1:22001/admin --eval 'config = { _id:"shard1", members:[{_id:0,host:"mongo1:22001",priority:1},{_id:1,host:"mongo2:22001",priority:2}, {_id:2,host:"mongo3:22001",arbiterOnly:true} ]}; rs.initiate(config);' ''')
            ## 配置shard2 replica-set
            run(
                ''' ./mongo/bin/mongo mongo2:22002/admin --eval 'config = { _id:"shard2", members:[ {_id:0,host:"mongo1:22002",arbiterOnly:true}, {_id:1,host:"mongo2:22002",priority:1}, {_id:2,host:"mongo3:22002",priority:2} ]}; rs.initiate(config);' ''')
            ## 配置shard3 replica-set
            run(
                ''' ./mongo/bin/mongo mongo3:22003/admin --eval 'config = { _id:"shard3", members:[ {_id:0,host:"mongo1:22003",priority:2}, {_id:1,host:"mongo2:22003",arbiterOnly:true}, {_id:2,host:"mongo3:22003",priority:1} ]}; rs.initiate(config);' ''')
            ## 将 replica-set加入shard集群
            run("sleep 90")
            print run(
                ''' ./mongo/bin/mongo mongo3:20000/admin --eval 'db.runCommand( { addshard : "shard1/mongo1:22001,mongo2:22001,mongo3:22001"}); db.runCommand( { addshard : "shard2/mongo1:22002,mongo2:22002,mongo3:22002"}); db.runCommand( { addshard : "shard3/mongo1:22003,mongo2:22003,mongo3:22003"}); ' ''')
            ## 添加索引
            print "添加索引"
            print run(
                '''  ./mongo/bin/mongo mongo3:20000/admin --eval 'db.runCommand( {listshards : 1 }); db.runCommand( { enablesharding :"xcloud"}); db.runCommand( { shardcollection : "xcloud.device_role",key : {_id: 1} } ); db.runCommand( { shardcollection : "xcloud.online",key : {uid: 1} } ); db.runCommand( { shardcollection : "xcloud.timer_task",key : {_id: 1} } );' ''')
            print run(
                '''  ./mongo/bin/mongo mongo3:20000/xcloud --eval 'db.online.dropIndex({ "uid":1 }); db.online.ensureIndex({uid:1},{unique:true});' ''')

            # mongo添加验证
            # 添加验证,第一个是xcloud的owner权限，第二个是xcloud的view权限    roles: [ { role: "userAdminAnyDatabase", db: "admin" }
            run(""" ./mongo/bin/mongo mongo3:20000/admin --eval 'db.createUser({user: "%s", pwd: "%s",  roles: [ "clusterAdmin","userAdminAnyDatabase","dbAdminAnyDatabase","readWriteAnyDatabase" ] } ) '  """ % (info['services']['mongo']['usrname'], info['services']['mongo']['pwd']))
            run(""" ./mongo/bin/mongo mongo3:20000/xcloud --authenticationDatabase admin -u %s  -p %s --eval 'db.createUser({user: "%s", pwd: "%s", roles: [ { role: "dbOwner", db: "xcloud" } ] }) ' """ % (info['services']['mongo']['usrname'], info['services']['mongo']['pwd'], info['services']['mongo']['usrname_view'], info['services']['mongo']['pwd_view']))

    '''
    # 伟大的注释
    进入任意一个mongodb机器
    ./mongo mongo1:22001/admin
     config = { _id:"shard1", members:[
    {_id:0,host:"mongo1:22001",priority:1},
    {_id:1,host:"mongo2:22001",priority:2},
    {_id:2,host:"mongo3:22001",arbiterOnly:true}
    ]};
     rs.initiate(config);

    ./mongo/bin/mongo mongo1:22001/admin --eval 'config = { _id:"shard1", members:[{_id:0,host:"mongo1:22001",priority:1},{_id:1,host:"mongo2:22001",priority:2}, {_id:2,host:"mongo3:22001",arbiterOnly:true} ]}; rs.initiate(config);'

    ./mongo mongo2:22002/admin
    config = { _id:"shard2", members:[
    {_id:0,host:"mongo1:22002",arbiterOnly:true},
    {_id:1,host:"mongo2:22002",priority:1},
    {_id:2,host:"mongo3:22002",priority:2}
    ]};
     rs.initiate(config);

    ./mongo/bin/mongo mongo2:22002/admin --eval 'config = { _id:"shard2", members:[ {_id:0,host:"mongo1:22002",arbiterOnly:true}, {_id:1,host:"mongo2:22002",priority:1}, {_id:2,host:"mongo3:22002",priority:2} ]}; rs.initiate(config);'

    ./mongo mongo3:22003/admin
    config = { _id:"shard3", members:[
    {_id:0,host:"mongo1:22003",priority:2},
    {_id:1,host:"mongo2:22003",arbiterOnly:true},
    {_id:2,host:"mongo3:22003",priority:1}
    ]};
     rs.initiate(config);

    ./mongo/bin/mongo mongo3:22003/admin --eval 'config = { _id:"shard3", members:[ {_id:0,host:"mongo1:22003",priority:2}, {_id:1,host:"mongo2:22003",arbiterOnly:true}, {_id:2,host:"mongo3:22003",priority:1} ]}; rs.initiate(config);'

    6 串联服务器和分配副本集
    ./mongo mongo1:20000/admin
    db.runCommand( { addshard : "shard1/mongo1:22001,mongo2:22001,mongo3:22001"});
    db.runCommand( { addshard : "shard2/mongo1:22002,mongo2:22002,mongo3:22002"});
    db.runCommand( { addshard : "shard3/mongo1:22003,mongo2:22003,mongo3:22003"});

    db.runCommand({listshards : 1 });

    db.runCommand( { enablesharding :"xcloud"});
    db.runCommand( { shardcollection : "xcloud.device_role",key : {_id: 1} } );
    db.runCommand( { shardcollection : "xcloud.online",key : {uid: 1}, {unique:true} } );
    db.runCommand( { shardcollection : "xcloud.timer_task",key : {_id: 1} } );


    ./mongo/bin/mongo mongo1:20000/admin 'db.runCommand( { addshard : "shard1/mongo1:22001,mongo2:22001,mongo3:22001"}); db.runCommand( { addshard : "shard2/mongo1:22002,mongo2:22002,mongo3:22002"}); db.runCommand( { addshard : "shard3/mongo1:22003,mongo2:22003,mongo3:22003"}); db.runCommand({listshards : 1 }); db.runCommand( { enablesharding :"xcloud"}); db.runCommand( { shardcollection : "xcloud.device_role",key : {_id: 1} } ); db.runCommand( { shardcollection : "xcloud.online",key : {uid: 1}, {unique:true} } ); db.runCommand( { shardcollection : "xcloud.timer_task",key : {_id: 1} } );'




    7 设置密码
    use admin;

    db.createUser(
      {
        user: "admin",
        pwd: "gomon@zktup",
        roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
      }
    );
    use xcloud;
    db.createUser(
    {
         user:"xcloud",
         pwd: "Xxdou@7K",
         roles:
           [
             { role: "dbOwner", db: "xcloud" }
           ]
       }
    );

    use admin; db.createUser( { user: "admin", pwd: "gomon@zktup", roles: [ { role: "userAdminAnyDatabase", db: "admin" } ] } );
    use xcloud; db.createUser( { user:"xcloud", pwd: "Xxdou@7K", roles: [ { role: "dbOwner", db: "xcloud" } ]} );



    ./mongo mongo1:20000/xcloud -u xcloud -p Xxdou@7K
    #设备id增加唯一索引
    db.online.dropIndex( { "uid":1 })
    db.online.ensureIndex({uid:1},{unique:true})

    ~/mongo/bin/mongo mongo3:20000/admin -u admin -p 123123
    db.runCommand({ listshards: 1})


    # 检验
    use xcloud
    db.online.getIndexes()

    ~/mongo/bin/mongo mongo3:20000/admin -u machtalk -p 123123

    ~/mongo/bin/mongo mongo3:20000/xcloud -u xcloud -p 123123



    '''

@task
@roles('mongo')
def mongo_clean():
    with cd(env.remote_dir):
        run("""
        ps aux | grep mongo | awk '{print $2}' | xargs -i kill -9 {}
        """)
        run("""
        rm -rf mongodb-linux-x86_64-2.6.11
        rm -rf mongo
        """)

@task
@roles('mongo')
def mongo_restart():
    with cd(env.remote_dir):
        run("""
        cd ./mongo/boot/
        ./restart
        """)

############ mongo 单机版
@task
@roles('mongo')
def mongo_single_deploy():
    pass

@task
@roles('mongo')
def mongo_single_restart():
    pass