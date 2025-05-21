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
3. Create a company at the company creation endpoint(http://localhost:8000/companies, method: POST) with the superuser account.
4. Create a company domain at the company domain creation endpoint(http://localhost:8000/companies/{company_id}/domains, method: POST) with the superuser account.
5. Create a user in the registration endpoint(http://localhost:8000/users, method: POST) with an email domain matching the company domain that was just created.
6. Log in at the login endpoint (http://localhost:8000/users/login, method: POST) using the user credentials to obtain the access token.
7. Create a job opening on the job creation endpoint(http://localhost:8000/jobs, method: POST) with the user account.(Can only create job openings for your own company)
8. Only the creator of a job opening or a superuser has permission to edit or delete it.
9. The endpoints for "Retrieve a list of all job postings"(http://localhost:8000/jobs, method: GET) and "Retrieve a single job posting by ID"(http://localhost:8000/jobs/{job_id}, method: GET)  do not necessarily require a token. Without a token, users can view all active job postings. With a token, users can also see the scheduled or expired job postings that they have created. Superusers can view all job postings regardless of their status.
10. The refresh token endpoint(http://localhost:8000/users/refresh_jwt, method: POST) can be used to obtain a new access token using the refresh token.
### Run tests locally
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
4. Run the tests
    ```bash
    docker compose run --rm app sh -c "pytest"
    ```
### Aspects that could be better
1. Adopt a microservices architecture by breaking down into separate microservices including authentication service, authorization service, job opening service, and establish an API gateway for unified frontend access.
2. Add an email verification feature to the registration process to ensure that users actually have access to the email address provided. Create an endpoint for account activation (when the user clicks the URL in the email, they will be redirected to the frontend, which will then call the account activation endpoint to activate the account).
   1. It is also possible to further develop a notification service to handle notification-related features.
   2. Message transmission between the authentication service and the notification service can be handled using Apache Kafka to enhance user experience and decouple the services.
3. Permission data can be stored in the database for easier configuration.