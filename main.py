import enum

import fastapi
import pydantic

from fastapi.staticfiles import StaticFiles


class ModelName(str, enum.Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


app = fastapi.FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    breakpoint()
    return {"message": "Hello World"}


@app.get("/testint/{param}")
async def testint(param: int, q: int | None = None):
    return {"message": param, "q": q}


@app.get("/testenum/{param}")
async def testenum(param: ModelName):
    return {"message": param}


class Item(pydantic.BaseModel):
    name: str
    email: pydantic.EmailStr


@app.post("/item/", response_model=Item)
async def add_item(item: Item):
    """Test docstring."""
    return item
