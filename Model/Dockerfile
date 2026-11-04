FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# CPU-only PyTorch wheels keep the image far smaller than the default (CUDA) ones.
COPY requirements.txt .
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY src ./src
COPY pretrained ./pretrained
# The API downloads the weights on first start if they aren't in pretrained/; the app may run
# as a non-root user (e.g. on Hugging Face Spaces), so make sure it can write there.
RUN chmod -R a+rwX pretrained

EXPOSE 7860
CMD ["uvicorn", "api:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "7860"]
