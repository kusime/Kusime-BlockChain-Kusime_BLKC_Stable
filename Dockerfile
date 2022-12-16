FROM python:alpine

# Install dependencies
RUN pip install Flask requests flask-cors
RUN pip install pycryptodome -i https://mirrors.aliyun.com/pypi/simple/

# Copy the current directory contents into the container at /app
COPY . /app

# Set the working directory to /app
WORKDIR /app


# Expose the Flask port
EXPOSE 6000

# Run the Flask app
# https://stackoverflow.com/questions/64954213/python-how-to-recieve-sigint-in-docker-to-stop-service
ENTRYPOINT ["python","NODE.py"]
