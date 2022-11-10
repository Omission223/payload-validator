# pulling python image

FROM python:3

# make a new directory inside container

RUN mkdir container-files

# add files inside the container

ADD flask_app.py requirements.txt /container-files/

# set the working directory to the newly made one

WORKDIR /container-files

# install dependancies

RUN pip install -r requirements.txt

# set environment variables

ENV FLASK_APP flask_app.py

# you can change the host name to the name you used for rabbitmq container

ENV AMQP_HOST rabbitmq

# login credentials

ENV AMQP_USER test
ENV AMQP_PASS test

#This will allow us to see the program output properly inside the terminal

ENV PYTHONUNBUFFERED=1

# expose ports

EXPOSE 5000

# finally, run the app on 0.0.0.0 IP A

CMD ["flask", "run", "-h", "0.0.0.0"]
