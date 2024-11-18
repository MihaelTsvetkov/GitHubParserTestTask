#!/bin/bash

set -e

SCRIPT_DIR=$(dirname "$(realpath "$0")")

echo "Скрипт находится в директории: $SCRIPT_DIR"

if [ ! -f ".env" ]; then
  echo "Ошибка: файл .env не найден."
  exit 1
fi

source .env

echo "Значения переменных окружения:"
echo "SERVICE_ACCOUNT_NAME=$SERVICE_ACCOUNT_NAME"
echo "FOLDER_ID=$FOLDER_ID"
echo "BUCKET_NAME=$BUCKET_NAME"
echo "FUNCTION_NAME=$FUNCTION_NAME"
echo "GITHUB_TOKEN=$GITHUB_TOKEN"
echo "POSTGRES_HOST=$POSTGRES_HOST"
echo "POSTGRES_USER=$POSTGRES_USER"
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo "POSTGRES_DB=$POSTGRES_DB"
echo "POSTGRES_PORT=$POSTGRES_PORT"
echo "CRON_SCHEDULE=$CRON_SCHEDULE"
echo "TRIGGER_NAME=$TRIGGER_NAME"


if [ -z "$SERVICE_ACCOUNT_NAME" ] || [ -z "$FOLDER_ID" ] || [ -z "$BUCKET_NAME" ] || [ -z "$FUNCTION_NAME" ] || [ -z "$GITHUB_TOKEN" ]; then
  echo "Ошибка: не удалось загрузить обязательные переменные окружения. Проверьте файл .env."
  exit 1
fi


if ! yc iam service-account get "$SERVICE_ACCOUNT_NAME" &>/dev/null; then
  if ! yc iam service-account create --name "$SERVICE_ACCOUNT_NAME" --folder-id "$FOLDER_ID"; then
    echo "Ошибка: не удалось создать сервисный аккаунт $SERVICE_ACCOUNT_NAME."
    exit 1
  fi
  echo "Сервисный аккаунт $SERVICE_ACCOUNT_NAME создан."
else
  echo "Сервисный аккаунт $SERVICE_ACCOUNT_NAME уже существует."
fi


if ! yc resource-manager folder add-access-binding "$FOLDER_ID" \
  --role "serverless.functions.invoker" \
  --service-account-name "$SERVICE_ACCOUNT_NAME"; then
  echo "Ошибка: не удалось назначить права для сервисного аккаунта $SERVICE_ACCOUNT_NAME."
  exit 1
fi
echo "Права для сервисного аккаунта $SERVICE_ACCOUNT_NAME успешно назначены."


if ! yc storage bucket get "$BUCKET_NAME" &>/dev/null; then
  if ! yc storage bucket create --name "$BUCKET_NAME"; then
    echo "Ошибка: не удалось создать бакет $BUCKET_NAME."
    exit 1
  fi
  echo "Бакет $BUCKET_NAME создан."
else
  echo "Бакет $BUCKET_NAME уже существует."
fi


if [ -d "cloud_function" ]; then
  cd cloud_function || exit
  if ! zip -r "${FUNCTION_NAME}.zip" github_parser.py requirements.txt; then
    echo "Ошибка: не удалось создать архив ${FUNCTION_NAME}.zip."
    exit 1
  fi
  echo "Архив ${FUNCTION_NAME}.zip создан."
else
  echo "Ошибка: директория cloud_function не найдена."
  exit 1
fi


if [ -f "${FUNCTION_NAME}.zip" ]; then
  if ! yc storage s3api put-object --bucket "$BUCKET_NAME" --key "${FUNCTION_NAME}.zip" --body "${FUNCTION_NAME}.zip"; then
    echo "Ошибка: не удалось загрузить архив ${FUNCTION_NAME}.zip в бакет $BUCKET_NAME."
    exit 1
  fi
  echo "Архив с кодом функции загружен в бакет $BUCKET_NAME."
else
  echo "Ошибка: архив ${FUNCTION_NAME}.zip не найден."
  exit 1
fi


if ! yc serverless function get "$FUNCTION_NAME" &>/dev/null; then
  if ! yc serverless function create --name "$FUNCTION_NAME" --folder-id "$FOLDER_ID"; then
    echo "Ошибка: не удалось создать функцию $FUNCTION_NAME."
    exit 1
  fi
  echo "Функция $FUNCTION_NAME создана."
else
  echo "Функция $FUNCTION_NAME уже существует."
fi


if ! yc serverless function version create \
  --function-name "$FUNCTION_NAME" \
  --runtime python312 \
  --entrypoint github_parser.handler \
  --memory 128m \
  --execution-timeout 240s \
  --environment GITHUB_TOKEN="$GITHUB_TOKEN" \
  --environment POSTGRES_HOST="$POSTGRES_HOST" \
  --environment POSTGRES_USER="$POSTGRES_USER" \
  --environment POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  --environment POSTGRES_DB="$POSTGRES_DB" \
  --environment POSTGRES_PORT="$POSTGRES_PORT" \
  --package-bucket-name "$BUCKET_NAME" \
  --package-object-name "${FUNCTION_NAME}.zip"; then
  echo "Ошибка: не удалось создать новую версию функции $FUNCTION_NAME."
  exit 1
fi
echo "Новая версия функции $FUNCTION_NAME развернута."


if ! yc serverless function allow-unauthenticated-invoke --name "$FUNCTION_NAME"; then
  echo "Ошибка: не удалось сделать функцию $FUNCTION_NAME публичной."
  exit 1
fi
echo "Функция $FUNCTION_NAME теперь публичная и доступна для вызова без аутентификации."


if ! yc serverless trigger get "$TRIGGER_NAME" &>/dev/null; then
  if ! yc serverless trigger create timer \
    --name "$TRIGGER_NAME" \
    --cron-expression "$CRON_SCHEDULE" \
    --invoke-function-name "$FUNCTION_NAME"; then
    echo "Ошибка: не удалось создать триггер $TRIGGER_NAME."
    exit 1
  fi
  echo "Триггер $TRIGGER_NAME создан с расписанием $CRON_SCHEDULE."
else
  echo "Триггер $TRIGGER_NAME уже существует."
fi

echo "Функция $FUNCTION_NAME успешно создана, триггер настроен."

