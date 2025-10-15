import uvicorn
import os
from app import app, APP_PORT

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=APP_PORT,
        log_level=os.getenv("LOG_LEVEL", "info")
    )
