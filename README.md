# Employee Compensation Service

A backend REST API for managing employee and department information and generating compensation-related reports.

Built using **Python, Azure Functions, and Azure SQL Database**.

## Overview

The Employee Compensation Service provides HTTP APIs to:

* Create, retrieve, update, and delete employees
* List employees with an optional department filter
* Calculate total company bonus
* Find employees without a bonus
* Calculate bonus percentages
* Analyze department bonus and salary information
* Rank employees by bonus
* Identify the highest-paid employees

All database operations are performed through the API. Clients do not access the database directly.

## Architecture

```text
Client
   │
   ▼
Azure Functions HTTP API
   │
   ▼
Azure SQL Database
```

## Technologies

* **Python 3.11**
* **Azure Functions**
* **Azure SQL Database**
* **Microsoft SQL Server**
* **pyodbc**
* **REST APIs**
* **SQL**

## Project Structure

```text
Fusion_Practices_Employee_Compensation_Service/
│
├── function_app.py
├── host.json
├── requirements.txt
├── local.settings.example.json
├── .gitignore
├── README.md
│
└── sql/
    ├── create_tables.sql
    └── seed_data.sql
```

## Prerequisites

* Python 3.11+
* Azure Functions Core Tools
* Microsoft ODBC Driver 18 for SQL Server
* Access to an Azure SQL Database

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the database connection

Create a copy of:

```text
local.settings.example.json
```

and name it:

```text
local.settings.json
```

Add the required Azure SQL connection string to the `SQL_CONNECTION_STRING` setting.

> `local.settings.json` is excluded from Git because it contains sensitive configuration.

## Database Setup

Run the SQL scripts in this order:

1. `sql/create_tables.sql` — creates the database tables and indexes
2. `sql/seed_data.sql` — inserts sample departments and employees

The database contains two main tables:

* **Department**
* **Employee**

The `Employee` table has a foreign-key relationship with `Department`.

## Run Locally

Start the Azure Functions application:

```bash
func start
```

The API will be available at:

```text
http://localhost:7071/api
```

## API Endpoints

### Employee CRUD

| Method   | Endpoint                        | Description                    |
| -------- | ------------------------------- | ------------------------------ |
| `POST`   | `/api/employees`                | Create an employee             |
| `GET`    | `/api/employees/{employee_id}`  | Get an employee by ID          |
| `GET`    | `/api/employees`                | List all employees             |
| `GET`    | `/api/employees?departmentId=1` | Filter employees by department |
| `PUT`    | `/api/employees/{employee_id}`  | Update an employee             |
| `DELETE` | `/api/employees/{employee_id}`  | Delete an employee             |

### Compensation Reports

| Method | Endpoint                                        | Description                                             |
| ------ | ----------------------------------------------- | ------------------------------------------------------- |
| `GET`  | `/api/reports/total-bonus`                      | Calculate total company bonus                           |
| `GET`  | `/api/reports/no-bonus`                         | Find employees without a bonus                          |
| `GET`  | `/api/reports/bonus-percentages`                | Calculate bonus percentage of salary                    |
| `GET`  | `/api/reports/departments-above-average-salary` | Find departments meeting the bonus/salary condition     |
| `GET`  | `/api/reports/bonus-ranking`                    | Rank employees by bonus                                 |
| `GET`  | `/api/reports/highest-salary`                   | Find highest base salary and highest total compensation |

## Business Rules

* `EmployeeID` is generated automatically by the database.
* Every employee must belong to an existing department.
* `Salary` is required.
* `Bonus` is optional and can be `NULL`.
* A `NULL` bonus is treated as `0` when calculating total compensation.
* Total compensation is calculated as:

```text
Salary + Bonus
```

* Bonus percentage is calculated as:

```text
(Bonus / Salary) × 100
```

* Bonus percentages are rounded to two decimal places.
* Employees with `NULL` bonuses appear last in the bonus ranking.
* Division by zero is prevented when calculating bonus percentages.

## Error Handling

The API handles invalid requests, missing records, database errors, and validation errors using appropriate HTTP status codes, including:

* `200 OK`
* `201 Created`
* `204 No Content`
* `400 Bad Request`
* `404 Not Found`
* `500 Internal Server Error`

## Security

* Database credentials are not hardcoded in the application.
* The SQL connection string is read from the `SQL_CONNECTION_STRING` environment setting.
* `local.settings.json` is excluded from source control.
* SQL queries use parameters for user-provided values.

## Bonus Default Decision

The database uses `NULL` to represent an employee with no recorded bonus.

A default 5% bonus is **not written into the database**, because doing so would change the stored business data.

If a 5% default is required for a specific calculation, it can instead be applied at read time while keeping the original database value unchanged.

## Testing

The API was tested locally using Azure Functions Core Tools and HTTP requests.

Testing covered:

* Employee creation
* Employee retrieval
* Employee listing
* Department filtering
* Employee update
* Employee deletion
* Total company bonus
* Employees without bonus
* Bonus percentages
* Department bonus analysis
* Bonus ranking
* Highest salary
* Highest total compensation
* Validation and error handling

## Submission Contents

```text
function_app.py              → Azure Functions API
requirements.txt             → Python dependencies
host.json                    → Azure Functions configuration
local.settings.example.json  → Example configuration
.gitignore                   → Excludes local files and secrets
README.md                    → Project documentation

sql/
├── create_tables.sql        → Database schema
└── seed_data.sql            → Sample data
```

## Author

**Supriya Kamthekar**

Computer Engineering Graduate | Data Science & AI/ML
