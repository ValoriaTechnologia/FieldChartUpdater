FROM python:3.12-slim

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY edit_yaml.py /edit_yaml.py

ENTRYPOINT ["python", "/edit_yaml.py"]
