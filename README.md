DemoShop + LogSherlock
======================

DemoShop is a small Flask-based sample application with a React frontend added for LogSherlock testing. It was created to generate predictable application events from real API calls so that LogSherlock can observe login, product, order, security, and system behavior end to end.

Why this project exists
-----------------------

The goal is not to replace the backend or introduce new business logic. The goal is to provide a simple user interface that exercises the existing DemoShop APIs and produces the same backend logs that LogSherlock already expects.

This makes the project useful for:

- validating login success and failure events
- testing product create, update, and delete flows
- triggering order placement and order failure paths
- generating unauthorized access logs
- checking system health and backend error handling

Architecture
------------

Demo UI -> Existing API -> Existing collector -> PostgreSQL -> LogSherlock

The frontend only calls the current Flask routes. No backend routes, models, database tables, or logging logic were changed for the UI.

Project structure
-----------------

- `run.py`: Flask application entry point
- `app/`: existing backend application code
- `frontend/`: new React + Vite UI for LogSherlock testing
- `logs/`: application log output
- `instance/`: Flask instance data

Main backend routes
-------------------

- `GET /`: welcome message
- `GET /health`: health check
- `GET /test-error`: intentional backend exception for testing error logs
- `GET /login`: login info message
- `POST /login`: authenticate a user and generate login logs
- `GET /profile`: protected profile lookup
- `GET /products`: list products
- `GET /products/<id>`: get one product
- `POST /products`: create a product
- `PUT /products/<id>`: update a product
- `DELETE /products/<id>`: delete a product
- `GET /orders`: list orders
- `GET /orders/<id>`: get one order
- `POST /orders`: place an order

Important note
--------------

DemoShop does not expose a cancel-order endpoint. The frontend cancel-order button uses the existing invalid-order failure path so LogSherlock still receives a real backend event without changing the API.

Logged events
-------------

The existing backend already emits these events:

- `APPLICATION_STARTED`
- `APPLICATION_STOPPED`
- `APPLICATION_ERROR`
- `HTTP_REQUEST`
- `HTTP_RESPONSE`
- `USER_LOGIN_SUCCESS`
- `USER_LOGIN_FAILED`
- `PRODUCT_CREATED`
- `PRODUCT_UPDATED`
- `PRODUCT_DELETED`
- `ORDER_PLACED`
- `ORDER_FAILED`
- `UNAUTHORIZED_ACCESS`

How to run
----------

Backend:

```powershell
Set-Location D:\DemoShop
.\venv\Scripts\Activate.ps1
python run.py
```

Frontend:

```powershell
Set-Location D:\DemoShop\frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, usually `http://localhost:5173`.

Build the frontend:

```powershell
Set-Location D:\DemoShop\frontend
npm run build
```

Default demo credentials
-----------------------

- Username: `admin`
- Password: `admin123`

Frontend pages
--------------

- Login page: sends the existing login request and stores the returned token for protected calls
- Product page: creates, updates, deletes, and lists products
- Order page: places orders and uses the existing failure path for cancel testing
- Security page: triggers unauthorized access against the protected profile route
- System page: calls health and error routes to exercise system behavior
- Activity panel: shows the latest generated events from the current session

Notes
-----

- The React app lives in `frontend/` and is isolated from the Flask backend.
- Development uses a Vite proxy so the frontend can call the Flask server without changing backend CORS behavior.
- The UI is intentionally simple and is meant for event generation and log verification, not production commerce flows.
