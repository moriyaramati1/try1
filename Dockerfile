FROM python:3.9

ENV FLASK_APP=friends.py

WORKDIR /pythonProject13

ADD . /pythonProject13/

RUN pip install Flask py2neo matplotlib pandas

CMD [ "python","./friends.py"]
