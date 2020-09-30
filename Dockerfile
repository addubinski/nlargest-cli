FROM python:3

WORKDIR /usr/src/app

RUN mkdir /var/nlargest
RUN mkdir /var/nlargest/cache

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN pip install .

CMD [ "/bin/bash" ]