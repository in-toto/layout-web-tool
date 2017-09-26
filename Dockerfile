FROM debian:stable-slim as builder
LABEL maintainer "root@shikherverma.com"
RUN apt-get update -y --fix-missing && \
  apt-get install -y --no-install-recommends ruby ruby-dev build-essential gnupg2 dirmngr curl && \
  gem install sass && \
  curl -sL https://deb.nodesource.com/setup_8.x | bash - && \
  apt-get install -y --no-install-recommends nodejs && \
  npm install -g gulp
COPY . /app
WORKDIR /app
RUN npm install && \
  sass static/scss/main.scss:static/css/main.scss.css -E "UTF-8" && \
  gulp

FROM debian:stable-slim
RUN apt-get update -y --fix-missing && \
  apt-get install -y --no-install-recommends python python-pip python-dev python-setuptools build-essential git mongodb && \
  pip install wheel
COPY --from=builder /app /app
WORKDIR /app
RUN pip install -r requirements.txt && \
  mkdir -p /data/db && \
  mkdir instance
EXPOSE 5000
CMD ["./docker-start.sh"]
