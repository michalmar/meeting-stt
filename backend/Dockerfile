FROM python:3-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


# Set the working directory in the container
WORKDIR /code

# COPY requirements.txt .
# RUN pip install --no-cache-dir --upgrade -r requirements.txt
# COPY . .


# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

COPY . /code
RUN uv sync --locked --no-dev
ENV PATH="/code/.venv/bin:$PATH"

# install ffmpeg for audio processing
RUN apt-get update && apt-get install -y ffmpeg


# Expose the port that the app will run on
EXPOSE 3100

# Command to run the application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3100", "--workers", "4"]