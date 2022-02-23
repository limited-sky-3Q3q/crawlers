FROM ubuntu
WORKDIR /usr/src/app
COPY . .
RUN cp sources.list /etc/apt/sources.list
RUN apt-get update \
    && apt-get install -y redis-server \
#    && (redis-server /usr/src/app/redis.conf &) \
    && apt-get install -y python3.6 \
                            python3-pip \
                            tesseract-ocr \
                            libtesseract-dev \
    && pip3 install --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple pip \
    && pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

#RUN  apt-get install -y redis-server
#RUN redis-server /usr/src/app/redis.conf &
WORKDIR /usr/src/app
CMD python3.6 docker_run.py