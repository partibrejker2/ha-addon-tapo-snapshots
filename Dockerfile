FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc libffi-dev libssl-dev curl \
    libgl1 libglib2.0-0 \
 && pip install opencv-python pydrive2 \
 && apt-get clean

COPY run.py /app/
WORKDIR /app

CMD ["python", "run.py"]
