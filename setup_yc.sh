#!/bin/bash


if [ -z "$YC_TOKEN" ]; then
  echo "ERROR: переменная окружения YC_TOKEN не установлена. Установите её и повторите попытку."
  exit 1
fi


if ! command -v yc &>/dev/null; then
  echo "ERROR: Yandex Cloud CLI (yc) не установлена. Установите её и повторите попытку."
  exit 1
fi


echo "Инициализация Yandex Cloud..."


yc init <<EOF
3
$YC_TOKEN
1
n
EOF


if [ $? -eq 0 ]; then
  echo "Yandex Cloud успешно настроен."
else
  echo "ERROR: Не удалось настроить Yandex Cloud. Проверьте токен или соединение с интернетом."
  exit 1
fi


if ! yc config profile list &>/dev/null; then
  echo "ERROR: Конфигурация Yandex Cloud не завершена. Проверьте настройки."
  exit 1
fi

echo "Yandex Cloud готов к использованию."

