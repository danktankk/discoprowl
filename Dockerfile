##<--########################################################
##               DiscoProwl - danktankk                    ##
########################################################-->##
FROM python:3.10-alpine

## ------[ Update apk repo & install common utils ]------  ##
RUN apk update && apk add --no-cache \
    bash \
    curl \
    vim \
    nano \
    git \
    wget \
    net-tools

## --------------------[ enable logs ]-------------------- ##
ENV PYTHONUNBUFFERED=1

## ---------------------[ location ]---------------------- ##
WORKDIR /app

## -----------------[ add python script ]----------------- ##
COPY discoprowl.py .

## -----[ Install required Python modules using pip ]----- ##
RUN pip install requests apprise

## --------------------[ run script ]--------------------- ##
CMD ["python3", "discoprowl.py"]
