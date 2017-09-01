FROM ubuntu:latest
MAINTAINER Shikher Verma "root@shikherverma.com"
RUN apt-get update -y --fix-missing
RUN apt-get install -y python python-pip python-dev build-essential git nodejs npm ruby ruby-dev
# Install Dependencies
RUN \
  apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10 && \
  echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' > /etc/apt/sources.list.d/mongodb.list && \
  apt-get update && \
  apt-get install -y mongodb-org && \
  rm -rf /var/lib/apt/lists/*
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN npm install --verbose
RUN gem install sass
EXPOSE 5000
CMD ["./docker-start.sh"]
