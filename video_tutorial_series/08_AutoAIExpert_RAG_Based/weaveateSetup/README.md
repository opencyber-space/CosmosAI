# Docker Compose Project

## Overview
This project utilizes Docker Compose to define and run multi-container Docker applications. It includes a Dockerfile for building the application image and a set of scripts for managing the project environment.


## Setup Instructions


1. **Create Necessary Folders:**
   Run the following script to create the required directories:
   ```
   bash create_folders.sh
   ```

2. **Run the Application:**
   Use the provided script to start the services defined in the `docker-compose.yml` file:
   ```
   bash run_docker_compose.sh
   ```

## Usage Guidelines
- Ensure Docker and Docker Compose are installed on your machine.
- Modify the `docker-compose.yml` and `Dockerfile` as needed to suit your application requirements.
- Use the scripts provided for easy management of the project environment.