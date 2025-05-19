# Итоговый проект «Фудграм»
## Описание

Проект «Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Стек технологий

- Backend: Python, Django REST Framework, PostgreSQL
- Frontend: React
- Контейнеризация: Docker
- Web-сервер: Nginx

## Запуск проекта

1. Клонировать репозиторий и перейти в него:
-   ```
    git clone https://github.com/ImToster/foodgram-st.git
    ```
-   ```
    cd foodgram-st
    ```

2. Перейти в папку `infra`:
-   ```
    cd infra
    ```

3. Создать файл `.env` и настроить в нём переменные окружения:
-   ```
    cp .env.example .env
    ```
    ```ini
    # .env
    POSTGRES_DB=foodgram
    POSTGRES_USER=foodgram_user
    POSTGRES_PASSWORD=foodgram_password
    DB_NAME=foodgram
    DB_HOST=db
    DB_PORT=5432

    SECRET_KEY=secret
    DJANGO_ALLOWED_HOSTS=127.0.0.1 localhost
    ```

4. Запустить контейнеры:
-   ```
    docker-compose up -d
    ```

Для остановки контейнеров выполнить:
```bash
docker-compose down
```

## Доступ к проекту:
- Главная страница: http://localhost
- Администрирование Django: http://localhost/admin
- API документация: http://localhost/api/docs/


## Docker образы

Созданные образы проекты доступны на Docker Hub по следующим именам:
- Backend: `acenes/foodgram_backend`
- Frontend: `acenes/foodgram_frontend` 

## Автор
Выполнил студент ЛЭТИ группы 2304 Жилин Денис Алексеевич.