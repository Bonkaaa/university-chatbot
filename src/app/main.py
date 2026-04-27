from fastapi import FastAPI
from .db import Base, engine
from .routes import auth_router, conversation_router, message_router

# Import models so SQLAlchemy registers them
from .models import user, conversation, message, session  # noqa

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chainlit Backend")

app.include_router(auth_router)
app.include_router(conversation_router)
app.include_router(message_router)

@app.get("/")
def root():
    return {"message": "Backend running"}