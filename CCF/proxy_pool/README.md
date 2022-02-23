# 很久没有维护了，不知道之前抓的几个免费代理网站现在质量如何，不确保能否抓取到有效代理了

# 在docker中使用

proxy_pool目录下

```shell
# 构建镜像
docker build -t my-proxy-pool .

# 运行容器
docker run -d -p 5010:5010 my-proxy-pool
```



# 访问服务

​	访问http://localhost:5010/查看详情

​	