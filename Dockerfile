FROM python:windowsservercore

WORKDIR /app

RUN python -m pip install --upgrade pip
RUN python -m pip install poetry

COPY . .

RUN python -m poetry install

EXPOSE 10443
CMD ["python", "-m", "poetry", "run", "waitress-serve", "--host", "0.0.0.0", "--port", "10443", "src.app:app"]