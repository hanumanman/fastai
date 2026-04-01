from enum import Enum

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/id/{id}")
async def read_id(id: int):
    return {"message": f"Hello, id {id}"}

class Item(str, Enum):
    a = "a"
    b = "b"
    c = "c"

@app.get("/enum/{arg}")
async def read_enum(arg: Item):
    if arg == Item.a:
        return {"enum a": "a"}
    elif arg == Item.b:
        return {"enum b": "b"}
    elif arg == Item.c:
        return {"enum c": "c"}
    else:
        return {"enum": "unknown"}

@app.get("/query")
async def read_query(q: str = "default"):
    return {"query": q}

class Thing(BaseModel):
    name: str
    desc: str

@app.post("/thing")
async def create_thing(thing: Thing):
    return {"name": thing.name, "desc": thing.desc}
