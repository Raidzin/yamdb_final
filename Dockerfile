FROM python:3.7-slim

RUN mkdir /api_yamdb

COPY api_yamdb/requirements.txt /api_yamdb

RUN pip install -r /api_yamdb/requirements.txt --no-cache-dir

COPY api_yamdb/ /api_yamdb

WORKDIR /api_yamdb

CMD ["gunicorn", "api_yamdb.api_yamdb.wsgi:application", "--bind", "0:8000" ]

