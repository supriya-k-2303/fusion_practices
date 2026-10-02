# Employee Compensation Service



## Overview



Employee Compensation Service is an HTTP-based backend service built using Azure Functions and Azure SQL Database.



The service manages employee and department records and provides compensation-related reports.



## Architecture



Client

→ Azure Functions HTTP API

→ Azure SQL Database



All database operations are performed through the API. Clients do not access the database directly.



## Technologies



\- Python 3.11

\- Azure Functions

\- Azure SQL Database

\- pyodbc

\- Microsoft SQL Server

\- REST APIs

\- SQL



## Project Structure



```text

Fusion\_practices/

│

├── function\_app.py

├── host.json

├── requirements.txt

├── local.settings.example.json

├── .gitignore

├── README.md

│

└── sql/

&#x20;   ├── create\_tables.sql

&#x20;   └── seed\_data.sql

Yes. **Copy everything inside this single code block** and paste it directly into `README.md`.

````markdown
# Employee Compensation Service

## Overview

Employee Compensation Service is an HTTP-based backend service built using Azure Functions and Azure SQL Database.

The service manages employee and department records and provides compensation-related reports.

## Architecture

Client
  ↓
Azure Functions HTTP API
  ↓
Azure SQL Database

All database operations are performed through the API. Clients do not access the database directly.

## Technologies

- Python 3.11
- Azure Functions
- Azure SQL Database
- pyodbc
- Microsoft SQL Server
- REST APIs
- SQL

## Project Structure

```text
Fusion_practices/
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
````

## Prerequisites

* Python 3.11+
* Azure Functions Core Tools
* Microsoft ODBC Driver 18 for SQL Server
* Azure SQL Database
* Python virtual environment

## Local Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Copy `local.settings.example.json` to `local.settings.json` and configure the Azure SQL connection string.

The actual `local.settings.json` file contains local secrets and is excluded from source control.

## Database Setup

Run the SQL scripts in the following order:

1. `sql/create_tables.sql`
2. `sql/seed_data.sql`

These scripts create the Department and Employee tables and insert sample data.

## Run the Application

Start Azure Functions locally:

```powershell
func start
```

The API will be available at:

```text
http://localhost:7071/api
```

## CRUD API Endpoints

### Create Employee

```text
POST /api/employees
```

Creates a new employee.

### Get Employee

```text
GET /api/employees/{employee_id}
```

Retrieves an employee by EmployeeID.

### List Employees

```text
GET /api/employees
```

Returns all employees.

Optional department filter:

```text
GET /api/employees?departmentId=1
```

### Update Employee

```text
PUT /api/employees/{employee_id}
```

Updates an employee's details.

### Delete Employee

```text
DELETE /api/employees/{employee_id}
```

Deletes an employee.

## Report Endpoints

### 1. Total Company Bonus

```text
GET /api/reports/total-bonus
```

Calculates the total company bonus while treating NULL bonuses as zero.

### 2. Employees Without Bonus

```text
GET /api/reports/no-bonus
```

Returns employees who have never received a bonus, represented by a NULL bonus value.

### 3. Employee Bonus Percentages

```text
GET /api/reports/bonus-percentages
```

Returns each employee's bonus and bonus percentage relative to their base salary.

The percentage is rounded to two decimal places.

### 4. Departments Above Average Salary

```text
GET /api/reports/departments-above-average-salary
```

Returns departments where the total department bonus is greater than the department's average base salary.

### 5. Bonus Ranking

```text
GET /api/reports/bonus-ranking
```

Ranks employees by bonus amount.

Employees with NULL bonuses are placed last.

### 6. Highest Salary Report

```text
GET /api/reports/highest-salary
```

Returns:

* Employee with the highest base salary
* Employee with the highest total compensation
* Whether the same employee has both

Total compensation is calculated as:

```text
Salary + Bonus
```

with NULL bonus treated as zero.

## Error Handling

The API returns appropriate HTTP status codes including:

* `200 OK`
* `201 Created`
* `204 No Content`
* `400 Bad Request`
* `404 Not Found`
* `500 Internal Server Error`

Invalid requests and database errors are handled gracefully.

Database credentials are not exposed in API responses.

## Security and Configuration

Database credentials are not hardcoded in the application.

The SQL connection string is loaded from the `SQL_CONNECTION_STRING` environment setting.

The actual `local.settings.json` file is excluded from source control through `.gitignore`.

A `local.settings.example.json` file is provided as a configuration template.

## Bonus Default Decision

The database stores NULL when an employee has no bonus.

The application does not automatically write a 5% bonus into the database because NULL represents the actual stored state.

If a default 5% bonus is required for a particular business calculation, it can be applied at read time while keeping the original database value unchanged.

This preserves the distinction between an employee having no recorded bonus and a calculated default bonus.

## Design Assumptions

* EmployeeID is generated automatically by the database.
* Every employee must belong to an existing department.
* DepartmentID is enforced using a foreign key.
* FirstName and LastName are required.
* Salary is required.
* Bonus is optional and can be NULL.
* HireDate is required.
* NULL bonus is treated as zero when calculating total compensation and total company bonus.
* Bonus percentage is calculated using base salary.
* Division by zero is prevented when calculating bonus percentage.
* SQL queries use parameters rather than dynamically constructing user-provided SQL values.

## Database Schema

### Department

| Column         | Type         | Description         |
| -------------- | ------------ | ------------------- |
| DepartmentID   | INT          | Primary key         |
| DepartmentName | VARCHAR(100) | Department name     |
| Location       | VARCHAR(100) | Department location |

### Employee

| Column       | Type          | Description               |
| ------------ | ------------- | ------------------------- |
| EmployeeID   | INT           | Primary key, identity     |
| FirstName    | VARCHAR(50)   | Employee first name       |
| LastName     | VARCHAR(50)   | Employee last name        |
| DepartmentID | INT           | Foreign key to Department |
| Salary       | DECIMAL(12,2) | Annual base salary        |
| Bonus        | DECIMAL(12,2) | Annual bonus, nullable    |
| HireDate     | DATE          | Employee hire date        |

## Testing

The API was tested locally using Azure Functions Core Tools and PowerShell HTTP requests.

Testing covered:

* Employee creation
* Employee retrieval
* Employee listing
* Department filtering
* Employee update
* Employee deletion
* Total company bonus report
* Employees without bonus report
* Bonus percentage report
* Department bonus report
* Bonus ranking
* Highest salary report
* Highest total compensation report
* HTTP error handling
* Department validation

## Submission Contents

The submission contains:

* `function_app.py` - Azure Functions application
* `requirements.txt` - Python dependencies
* `host.json` - Azure Functions configuration
* `local.settings.example.json` - Example local configuration
* `.gitignore` - Excludes local settings, virtual environment and generated files
* `README.md` - Project documentation
* `sql/create_tables.sql` - Database schema and indexes
* `sql/seed_data.sql` - Sample database data

```
```

