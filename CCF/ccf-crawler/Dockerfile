FROM python:3.6
WORKDIR /usr/src/app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
CMD python ccf_crawler.py