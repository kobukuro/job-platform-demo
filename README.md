# job-platform-demo

## Backend
### Run locally
#### Prerequisites
Install Docker and Docker Compose
#### Steps
1. Clone the repository
    ```bash
    git clone https://github.com/kobukuro/job-platform-demo.git
   ```
2. Navigate to root directory
    ```bash
    cd job-platform-demo
    ```
3. Navigate to backend directory
    ```bash
    cd job-platform-demo-backend
    ```
4. Build and run the containers
    ```bash
   docker compose up -d --build
   ```
API docs are available at `http://localhost:8000/docs`
### Usage
1. Create a superuser
    ```bash
    docker compose run --rm app sh -c "python manage.py createsuperuser"
    ```
2. Log in at the login endpoint (http://localhost:8000/users/login, method: POST) using superuser credentials to obtain the access token.
   
   In this system, only accounts belonging to a specific company (for example, Company A) can create job openings for that company. Therefore, we need to use a superuser account to first create the company and its domain.
3. Create a company at the company creation endpoint(http://localhost:8000/companies/{company_id}/domains, method: POST) with the superuser account.
4. Create a company domain at the company domain creation endpoint( ) with the superuser account.