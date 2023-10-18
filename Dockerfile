FROM python:3.8-slim-buster
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Collect static files and migrate the database
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

# Start the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "fileapp.wsgi:application"]
