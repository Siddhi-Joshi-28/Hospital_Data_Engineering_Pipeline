FROM python:3.11-slim

WORKDIR /app

# Only the packages Streamlit needs (keeps the image small)
RUN pip install --no-cache-dir streamlit==1.35.0 plotly==5.22.0 pandas==2.2.2 \
    SQLAlchemy==2.0.30 psycopg2-binary==2.9.9

COPY streamlit_app.py .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
