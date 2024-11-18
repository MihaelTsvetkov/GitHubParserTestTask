FROM python:3.12-alpine

RUN apk update && \
    apk add --no-cache bash curl unzip build-base expect zip && \
    rm -rf /var/cache/apk/*

RUN curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash && \
    ln -s /root/yandex-cloud/bin/yc /usr/local/bin/yc

COPY . /fastapiproject/
WORKDIR /fastapiproject

COPY setup_yc_expect.sh /fastapiproject/setup_yc_expect.sh
COPY setup_yc.sh /fastapiproject/setup_yc.sh
COPY deploy_yc_function.sh /fastapiproject/deploy_function.sh
COPY start.sh /fastapiproject/start.sh

RUN chmod +x /fastapiproject/setup_yc_expect.sh /fastapiproject/setup_yc.sh /fastapiproject/deploy_function.sh /fastapiproject/start.sh

RUN pip install --no-cache-dir -r /fastapiproject/requirements.txt

ARG CLOUD_ID
ARG FOLDER_ID
ARG YC_TOKEN
ARG SERVICE_ACCOUNT_NAME
ARG FUNCTION_NAME
ARG TRIGGER_NAME
ARG BUCKET_NAME

ENV CLOUD_ID=${CLOUD_ID} \
    FOLDER_ID=${FOLDER_ID} \
    YC_TOKEN=${YC_TOKEN} \
    SERVICE_ACCOUNT_NAME=${SERVICE_ACCOUNT_NAME} \
    FUNCTION_NAME=${FUNCTION_NAME} \
    TRIGGER_NAME=${TRIGGER_NAME} \
    BUCKET_NAME=${BUCKET_NAME}

RUN /fastapiproject/start.sh

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
