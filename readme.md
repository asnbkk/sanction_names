# Сервис извлечения стемм

Простой сервис на FastAPI для получения уникальных корней (стемм) из русского текста.

## Установка и запуск

1. Клонируйте репозиторий:

   ```bash
   git clone <URL>
   cd <папка_проекта>
   ```
2. Создайте и активируйте виртуальное окружение:

   ```bash
   python3 -m venv venv
   source venv/bin/activate    # Linux/macOS
   # .\venv\Scripts\Activate.ps1   # PowerShell на Windows
   ```
3. Установите зависимости:

   ```bash
   pip install fastapi uvicorn keybert sentence-transformers nltk
   ```
4. Запустите сервис:

   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

Сервис будет доступен на **[http://localhost:8000](http://localhost:8000)**.

## Эндпоинты

* **GET /health** — проверка работы сервиса. Ответ: `{"status":"ok"}`
* **GET /status** — статус загрузки моделей (percent от 0 до 100).
* **POST /extract** — извлечение стемм.

  **Тело запроса (JSON):**

  ```json
  {
    "doc": "ваш текст",
    "top_n": 5,
    "min_ngram": 1,
    "max_ngram": 1
  }
  ```

  **Ответ:**

  ```json
  {"stems": [["корень1", 0.75], ["корень2", 0.60], ...]}
  ```

## Пример использования

```bash
curl -X POST http://localhost:8000/extract \
     -H "Content-Type: application/json" \
     -d '{"doc":"Ракообразные живые и копченые","top_n":3,"min_ngram":1,"max_ngram":1}'
```

## Docker (опционально)

1. Соберите образ:

   ```bash
   docker build -t stem-service .
   ```
2. Запустите контейнер:

   ```bash
   docker run -d -p 8000:8000 stem-service
   ```

---