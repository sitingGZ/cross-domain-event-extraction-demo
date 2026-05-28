FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install --upgrade pip \
    && pip install torch==2.9.0 torchvision==0.24.0 torchaudio==2.9.0 --index-url https://download.pytorch.org/whl/cu130 \
    && pip install dash dash-bootstrap-components transformers sentencepiece protobuf

COPY . /app

EXPOSE 8051

CMD ["python", "web_api_dash_app.py"]
