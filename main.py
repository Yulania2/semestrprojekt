from views import app
from db import Base, engine

# Створення таблиць
Base.metadata.create_all(bind=engine)

# Запуск серверу
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5007, reload=True)
