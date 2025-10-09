# Module 6: Deploy Anywhere
Name: Holly Kipouros (hkipour1)
SSH url to GitHub repo:  git@github.com:HKipouros/jhu_software_concepts.git
url to Dockerhub repo: https://hub.docker.com/repositories/hollykipouros

## Run Instructions
### 1. Install Docker
Install [Docker] (https://docs.docker.com/get-docker/) on your machine.
### 2. Download Images
Download the following images:
- `YOUR_DOCKERHUB_USERNAME/module_6-worker:latest` – Worker service image
- `YOUR_DOCKERHUB_USERNAME/module_6-web:latest` – Web service image
- `YOUR_DOCKERHUB_USERNAME/postgres:17` – PostgreSQL database image
- `YOUR_DOCKERHUB_USERNAME/rabbitmq:3.13-management` – RabbitMQ image
### 3. Download the repository and install required packages
The Module_6 repository is available at the Github url above.
Install Python and required packages found in the requirements.txt file.
### 4. Run the application
After completing all downloads, use Docker Compose to run:
docker-compose up
### Ports
RabbitMQ: 15672:15672
Web: 8080:8080

## Development Approach
I initially reformatted my code from Module_5 into project structure defined by this week's assignment, including "web" and "worker" folders, and reformatted the Python modules to run on my local machine using the new folder structure. I then generated Dockerfiles for the web and worker containers and a docker-compose.yml file using the assignment template as a starting point. I generated publisher.py to publish messages and updated pages_bp.py (blueprint module for a Flask app) to call publish_task functions for data handling rather than running the data handling directly. Next, consumer.py was generated to listen for the generated messages, determine the task type, and call data handling functions as needed. I also updated load_data.py to generate a watermark table, and I further consumer.py to take in an entry from the watermark table to ensure unique inserts.

