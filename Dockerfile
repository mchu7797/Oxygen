FROM mcr.microsoft.com/windows/servercore:ltsc2022

LABEL Description="Oxygen" Vendor="csmd_" Version="0.1"

RUN powershell -NoProfile -ExecutionPolicy Bypass -Command  \
  "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; \
   Invoke-RestMethod 'https://astral.sh/uv/install.ps1' | Invoke-Expression"

COPY . /app
WORKDIR /app

RUN uv venv
RUN uv sync

EXPOSE 10443
CMD ["uv", "run", "waitress-serve", "--host", "0.0.0.0", "--port", "10443", "src.app:app"]
