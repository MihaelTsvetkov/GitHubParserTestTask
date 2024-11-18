#!/bin/bash

if [ -z "$SERVICE_ACCOUNT_NAME" ]; then
  echo "ERROR: переменная окружения SERVICE_ACCOUNT_NAME не установлена."
  exit 1
fi

echo "Инициализация Yandex Cloud..."

yc init <<EOF
2
$SERVICE_ACCOUNT_NAME
$YC_TOKEN
1
n
EOF

if [ $? -eq 0 ]; then
  echo "Yandex Cloud profile '$SERVICE_ACCOUNT_NAME' успешно настроен."
else
  echo "Ошибка настройки профиля Yandex Cloud."
  exit 1
fi
