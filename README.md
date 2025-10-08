# 🐢 TurtlyScope

**TurtlyScope** is an interactive web tool for **visualizing RDF graphs** written in **Turtle (TTL)** format.
It transforms plain RDF triples into a network diagram, helping you quickly explore relationships between subjects, predicates, and objects.

At its core, TurtlyScope provides:

## **Getting started**

If you don't want to use `uv` you can set up a virtual environment explicitly

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

```

## **Run the Server from shell**

**Using `uv`**
```sh
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Without `uv` you need to set up the virtual environment and activate it before you can proceed with:

```sh
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## **Run the Server from Docker**

```sh
docker build -t turtlyscope:latest .
docker run -d --name turtlyscope -p 8000:8000 turtlyscope:latest
```
