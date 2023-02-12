FROM python:3.9
WORKDIR /app
# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements/local.txt /app/requirements/local.txt
RUN pip install -r requirements/local.txt
COPY . /app
ENTRYPOINT [ "python" ]
CMD [ "app/api.py" ]
