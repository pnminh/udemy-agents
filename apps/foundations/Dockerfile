FROM python:3.10-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./ 

RUN uv sync --system-type=linux

COPY . . 

EXPOSE 7860

CMD ["uv", "run", "python", "app.py"]