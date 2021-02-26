#进程数
workers = 5

# 指定每个工作的线程数
threads = 5

# 监听端口8000
bind = '0.0.0.0:80'
 
# 最大并发量
worker_connections = 2000
 
# 进程文件
pidfile = '/var/run/gunicorn.pid'
 
# 访问日志和错误日志
accesslog = '/var/log/gunicorn_acess.log'
errorlog = '/var/log/gunicorn_error.log'
 
# 日志级别
loglevel = 'info'

#工作模式
worker_class="gevent"
