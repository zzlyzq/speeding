# speeding
加速部署过程，python fabric集成框架。

# 核心目标
* 不论是单机版本，还是集群版本，让重复的私有云部署code化
* 每次只需要修改fabric.py里面的info这个json，提供定制化的信息

# 常用发布命令

| 安装软件 | 执行命令 | 备注 |
| -- | -- | -- |
| basic | fab basic_deploy | 建立账户，调整参数等 |
| fdfs | fab fdfs_deploy | |
| redis | fab redis_deploy | |
| zookeeper | fab zookeeper_putfile; fab zookeeper_deploy | | 
| rabbitmq | fab rabbitmq_putfile; fab rabbitmq_deploy | |
| mariadb | fab mariadb_putfile; fab mariadb_deploy | |
| rabbitmq | fab rabbitmq_putfile; fab rabbitmq_deploy |
| mongodb | fab mongo_single_deploy | | 
