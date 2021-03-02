# mini-flaskblog
该程序使用pypy代替python3，并使用了gunicorn+gevent启动项目。<br>

python3基础启动：<br>
安装依赖包：pip install -r requirements.txt<br>
启动项目：python3 manager.py<br>
后台用户名密码：sibajie sibajie25
<br>
本代码支持全站redis缓存，如果需要使用，按如下操作。<br>
centos7为例：<br>
yum install redis<br>
systemctl start redis<br>
进入项目目录，pypy/bin/pip install redis
执行start.sh启动。<br>
默认为5进程，5线程，redis永久缓存。
<br><br>
演示地址：blog.bj.cn
<br><br>
