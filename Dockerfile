FROM python:3.14-slim
WORKDIR /app
COPY requirements-lock.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY src ./src
COPY sql ./sql
COPY data ./data
COPY app.py ./
RUN pip install --no-cache-dir --no-deps .
# Repository-relative research assets require src layout at runtime.
ENV PYTHONPATH=/app/src
EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]
