FROM python:alpine3.20

RUN apk update && apk upgrade
RUN python -m pip install --upgrade pip

# Create a hexogen group and user 
RUN addgroup -S hexogen && adduser -S hexogen -G hexogen -h /home/hexogen
USER hexogen

RUN pip install virtualenv
COPY ./python/hexogen.py /workspace/hexogen.py
COPY ./python/requirements.txt /workspace/requirements.txt

RUN pip install -r /workspace/requirements.txt

ENTRYPOINT python3 /workspace/hexogen.py
