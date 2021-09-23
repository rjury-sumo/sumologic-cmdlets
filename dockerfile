FROM python:3

WORKDIR /usr/src/app
COPY . .
#RUN pip install pipenv 
#RUN pipenv install --system --deploy --ignore-pipfile
#RUN pipenv lock -r > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# for sumoquerystream
ENV SUMO_END='au'
ENV DEFAULT_RANGE='5m'
ENV DEFAULT_QUERY='* | timeslice 1m | _view as index | sum(_size) as bytes,count as events by _sourcecategory,_collector,_source,_timeslice'
ENV TIMESTAMP_STRATEGY='timeslice'

#CMD [ "/bin/bash" ]
CMD [ "python", "./bin/run/sumoquerystream.py" ]
