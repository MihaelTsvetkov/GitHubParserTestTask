#!/bin/bash

check_last_command() {
  if [ $? -ne 0 ]; then
    echo "ERROR: Последняя команда завершилась с ошибкой. Прерываем выполнение."
    exit 1
  fi
}

while true; do
  echo "Запуск setup_yc_expect.sh..."
  /fastapiproject/setup_yc_expect.sh | tee result.log
  check_last_command

  existing_profile_message=$(grep "it already exists" result.log || true)
  if [ -n "$existing_profile_message" ]; then
    echo "Обнаружено сообщение: $existing_profile_message"
    echo "Профиль уже существует. Запускаем setup_yc.sh для продолжения настройки..."
    /fastapiproject/setup_yc.sh
    check_last_command
    break
  fi

  if grep -q 'успешно настроен' result.log; then
    echo "Настройка успешно завершена."
    break
  else
    echo "Ошибка при настройке, повторяем попытку через 5 секунд..."
    sleep 5
  fi
done

echo "Запуск деплоя..."
if /fastapiproject/deploy_function.sh; then
  echo "Deploy завершен успешно."
else
  echo "ERROR: Не удалось выполнить деплой. Проверьте лог или настройки."
  exit 1
fi

if [ -z "$YC_TOKEN" ]; then
  echo "ERROR: Переменная окружения YC_TOKEN не установлена. Проверьте её значение."
  exit 1
fi

echo "Используем токен Yandex Cloud: $YC_TOKEN"
