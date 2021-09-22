FROM python:3

WORKDIR /usr/src/app
COPY . .
#RUN pip install pipenv 
#RUN pipenv install --system --deploy --ignore-pipfile
#RUN pipenv lock -r > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "/bin/bash" ]
#CMD [ "python", "./bin/run/sumoquery.py -q '* | count by _sourcecategory' -a $SUMO_UID:$SUMO_KEY -e 'xxx' -v 10 -t 'test'" ]
