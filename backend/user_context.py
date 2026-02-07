from contextvars import ContextVar

# ContextVar to hold the current user ID for the request
user_id_context: ContextVar[str] = ContextVar("user_id", default="guest")

def set_user_context(user_id: str):
    user_id_context.set(user_id)

def get_user_context() -> str:
    return user_id_context.get()
