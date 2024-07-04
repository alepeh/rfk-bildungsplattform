FROM python:3.11-slim

ARG PGDATABASE
ARG PGHOST
ARG PGPORT
ARG PGUSER
ARG PGPASSWORD

ENV PGDATABASE=$PGDATABASE
ENV PGHOST=$PGHOST
ENV PGPORT=$PGPORT
ENV PGUSER=$PGUSER
ENV PGPASSWORD=$PGPASSWORD

# install nginx
RUN apt-get update && apt-get install default-libmysqlclient-dev gcc nginx -y
# copy our nginx configuration to overwrite nginx defaults
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf
# link nginx logs to container stdout
RUN ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log

# copy the django code
COPY requirements.txt ./app/
COPY entrypoint.sh ./app/
COPY nginx/ ./app/nginx/
COPY bildungsplattform/ ./app/bildungsplattform/
COPY core/ ./app/core/
COPY erweiterungen/ ./app/erweiterungen

COPY manage.py ./app/

# change our working directory to the django projcet roo
WORKDIR /app

RUN python -m venv /opt/venv && \
    /opt/venv/bin/python -m pip install pip --upgrade && \
    /opt/venv/bin/python -m pip install -r requirements.txt
RUN /opt/venv/bin/python manage.py collectstatic
RUN /opt/venv/bin/python manage.py migrate

EXPOSE 8000

# make our entrypoint.sh executable
RUN chmod +x entrypoint.sh

# execute our entrypoint.sh file
CMD ["./entrypoint.sh"]