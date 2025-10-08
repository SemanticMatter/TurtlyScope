# 🐢 TurtlyScope

**TurtlyScope** is an interactive web tool for **visualizing RDF graphs** written in **Turtle (TTL)** format.
It transforms plain RDF triples into a network diagram, helping you quickly explore relationships between subjects, predicates, and objects.

At its core, TurtlyScope provides:
## **Getting started**

```bash
git clone <your-repo-url> turtlyscope
cd turtlyscope

python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

```

## **Run the Server from shell**

```sh
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## **Run the Server from Docker**

```sh
docker build -t turtlyscope:latest .
docker run -d --name turtlyscope -p 8000:8000 turtlyscope:latest
```
