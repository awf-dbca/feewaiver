# Prepare the base environment.
FROM ubuntu:20.04 as builder_base_feewaiver
MAINTAINER asi@dbca.wa.gov.au
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Australia/Perth
ENV PRODUCTION_EMAIL=True
ENV SECRET_KEY="ThisisNotRealKey"

RUN apt-get clean
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install --no-install-recommends -y wget curl git libmagic-dev gcc binutils libproj-dev gdal-bin python3 python3-setuptools python3-dev python3-pip tzdata cron rsyslog gunicorn libreoffice
RUN apt-get -y install ca-certificates
RUN apt-get install --no-install-recommends -y libpq-dev patch
RUN apt-get install --no-install-recommends -y postgresql-client mtr htop vim ssh
RUN apt-get install --no-install-recommends -y npm bzip2
RUN update-ca-certificates

# install node 16
RUN touch install_node.sh
RUN curl -fsSL https://deb.nodesource.com/setup_16.x -o install_node.sh
RUN chmod +x install_node.sh && ./install_node.sh
RUN apt-get install -y nodejs


RUN ln -s /usr/bin/python3 /usr/bin/python 
#&& \
 #   ln -s /usr/bin/pip3 /usr/bin/pip
RUN pip install --upgrade pip
# Install Python libs from requirements.txt.
FROM builder_base_feewaiver as python_libs_feewaiver
WORKDIR /app
#RUN touch /app/git_hash
#COPY .git/refs/heads/main /app/git_hash
COPY requirements.txt ./
#COPY git_history_recent ./
RUN touch /app/rand_hash
RUN pip install --no-cache-dir -r requirements.txt \
  # Update the Django <1.11 bug in django/contrib/gis/geos/libgeos.py
  # Reference: https://stackoverflow.com/questions/18643998/geodjango-geosexception-error
  #&& sed -i -e "s/ver = geos_version().decode()/ver = geos_version().decode().split(' ')[0]/" /usr/local/lib/python3.6/dist-packages/django/contrib/gis/geos/libgeos.py \
  && rm -rf /var/lib/{apt,dpkg,cache,log}/ /tmp/* /var/tmp/*

COPY libgeos.py.patch /app/
RUN patch /usr/local/lib/python3.8/dist-packages/django/contrib/gis/geos/libgeos.py /app/libgeos.py.patch
RUN rm /app/libgeos.py.patch

# Install the project (ensure that frontend projects have been built prior to this step).
FROM python_libs_feewaiver

COPY gunicorn.ini manage_fw.py ./
#COPY ledger ./ledger
COPY timezone /etc/timezone
ENV TZ=Australia/Perth
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN touch /app/.env
COPY .git ./.git
COPY feewaiver ./feewaiver
RUN cd /app/feewaiver/frontend/feewaiver; npm install
RUN cd /app/feewaiver/frontend/feewaiver; npm run build
RUN python manage_fw.py collectstatic --noinput

RUN mkdir /app/tmp/
RUN chmod 777 /app/tmp/

COPY cron /etc/cron.d/dockercron
COPY startup.sh /
## Cron start
RUN service rsyslog start
RUN chmod 0644 /etc/cron.d/dockercron
RUN crontab /etc/cron.d/dockercron
RUN touch /var/log/cron.log
RUN service cron start
RUN chmod 755 /startup.sh
# cron end

# IPYTHONDIR - Will allow shell_plus (in Docker) to remember history between sessions
RUN export IPYTHONDIR=/app/logs/.ipython/

EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
CMD ["/startup.sh"]
