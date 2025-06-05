from fastapi import FastAPI, Request
from apis.whatsapp import router as whatsapp_router

# Create an instance of the FastAPI class
# This 'app' object will be our main point of interaction to create all of our API.
app = FastAPI()

# Include the WhatsApp router into our main application
# This means all endpoints defined in whatsapp_router will be accessible through 'app'
# We'll add a prefix here so all whatsapp endpoints start with /whatsapp
app.include_router(whatsapp_router, prefix="/whatsapp")


# This is a "path operation decorator".
# It tells FastAPI that the function below is in charge of handling
# requests that go to:
# - the path "/" (the root path)
# - using a "get" operation
@app.get("/")
def read_root():
    """
    This function will be called whenever a user visits the root of our web application.
    The dictionary it returns will be automatically converted to JSON format and sent
    back to the browser.
    """
    return {"Hello": "World"}