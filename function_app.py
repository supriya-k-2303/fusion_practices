import os
import json
import pyodbc
import azure.functions as func


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


# ---------------------------------------------------------
# Database connection
# ---------------------------------------------------------

def get_connection():
    connection_string = os.getenv("SQL_CONNECTION_STRING")

    if not connection_string:
        raise Exception("SQL_CONNECTION_STRING is not configured.")

    return pyodbc.connect(connection_string)


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def employee_to_dict(row):
    return {
        "EmployeeID": row.EmployeeID,
        "FirstName": row.FirstName,
        "LastName": row.LastName,
        "DepartmentID": row.DepartmentID,
        "Salary": float(row.Salary),
        "Bonus": float(row.Bonus) if row.Bonus is not None else None,
        "HireDate": row.HireDate.isoformat()
    }


def json_response(data, status_code=200):
    return func.HttpResponse(
        json.dumps(data, default=str),
        status_code=status_code,
        mimetype="application/json"
    )


# =========================================================
# EMPLOYEE CRUD
# =========================================================


# ---------------------------------------------------------
# CREATE EMPLOYEE
# POST /api/employees
# ---------------------------------------------------------

@app.route(route="employees", methods=["POST"])
def create_employee(req: func.HttpRequest) -> func.HttpResponse:

    try:
        data = req.get_json()

        required_fields = [
            "FirstName",
            "LastName",
            "DepartmentID",
            "Salary",
            "HireDate"
        ]

        missing_fields = [
            field for field in required_fields
            if field not in data
        ]

        if missing_fields:
            return json_response(
                {
                    "error": "Missing required fields",
                    "fields": missing_fields
                },
                400
            )

        first_name = data["FirstName"]
        last_name = data["LastName"]
        department_id = data["DepartmentID"]
        salary = data["Salary"]
        bonus = data.get("Bonus")
        hire_date = data["HireDate"]

        connection = get_connection()
        cursor = connection.cursor()

        # Check whether department exists
        cursor.execute(
            """
            SELECT DepartmentID
            FROM Department
            WHERE DepartmentID = ?
            """,
            department_id
        )

        if cursor.fetchone() is None:
            connection.close()

            return json_response(
                {
                    "error": "Department does not exist",
                    "DepartmentID": department_id
                },
                400
            )

        cursor.execute(
            """
            INSERT INTO Employee
            (
                FirstName,
                LastName,
                DepartmentID,
                Salary,
                Bonus,
                HireDate
            )
            OUTPUT INSERTED.EmployeeID
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            first_name,
            last_name,
            department_id,
            salary,
            bonus,
            hire_date
        )

        employee_id = cursor.fetchone()[0]

        connection.commit()
        connection.close()

        return json_response(
            {
                "message": "Employee created successfully",
                "EmployeeID": employee_id
            },
            201
        )

    except ValueError:
        return json_response(
            {"error": "Invalid JSON request body"},
            400
        )

    except pyodbc.IntegrityError as e:
        return json_response(
            {
                "error": "Database integrity error",
                "details": str(e)
            },
            400
        )

    except Exception as e:
        return json_response(
            {
                "error": "Internal server error",
                "details": str(e)
            },
            500
        )


# ---------------------------------------------------------
# GET EMPLOYEE BY ID
# GET /api/employees/{employee_id}
# ---------------------------------------------------------

@app.route(route="employees/{employee_id}", methods=["GET"])
def get_employee(req: func.HttpRequest) -> func.HttpResponse:

    try:
        employee_id = int(req.route_params.get("employee_id"))

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                EmployeeID,
                FirstName,
                LastName,
                DepartmentID,
                Salary,
                Bonus,
                HireDate
            FROM Employee
            WHERE EmployeeID = ?
            """,
            employee_id
        )

        row = cursor.fetchone()
        connection.close()

        if row is None:
            return json_response(
                {
                    "error": "Employee not found",
                    "EmployeeID": employee_id
                },
                404
            )

        return json_response(employee_to_dict(row))

    except ValueError:
        return json_response(
            {"error": "EmployeeID must be an integer"},
            400
        )

    except Exception as e:
        return json_response(
            {
                "error": "Internal server error",
                "details": str(e)
            },
            500
        )


# ---------------------------------------------------------
# LIST EMPLOYEES
# GET /api/employees
# GET /api/employees?departmentId=1
# ---------------------------------------------------------

@app.route(route="employees", methods=["GET"])
def list_employees(req: func.HttpRequest) -> func.HttpResponse:

    try:
        department_id = req.params.get("departmentId")

        connection = get_connection()
        cursor = connection.cursor()

        if department_id:

            try:
                department_id = int(department_id)
            except ValueError:
                connection.close()

                return json_response(
                    {"error": "departmentId must be an integer"},
                    400
                )

            cursor.execute(
                """
                SELECT
                    EmployeeID,
                    FirstName,
                    LastName,
                    DepartmentID,
                    Salary,
                    Bonus,
                    HireDate
                FROM Employee
                WHERE DepartmentID = ?
                ORDER BY EmployeeID
                """,
                department_id
            )

        else:

            cursor.execute(
                """
                SELECT
                    EmployeeID,
                    FirstName,
                    LastName,
                    DepartmentID,
                    Salary,
                    Bonus,
                    HireDate
                FROM Employee
                ORDER BY EmployeeID
                """
            )

        rows = cursor.fetchall()
        connection.close()

        employees = [
            employee_to_dict(row)
            for row in rows
        ]

        return json_response(employees)

    except Exception as e:
        return json_response(
            {
                "error": "Internal server error",
                "details": str(e)
            },
            500
        )


# ---------------------------------------------------------
# UPDATE EMPLOYEE
# PUT /api/employees/{employee_id}
# ---------------------------------------------------------

@app.route(route="employees/{employee_id}", methods=["PUT"])
def update_employee(req: func.HttpRequest) -> func.HttpResponse:

    try:
        employee_id = int(req.route_params.get("employee_id"))

        data = req.get_json()

        required_fields = [
            "FirstName",
            "LastName",
            "DepartmentID",
            "Salary",
            "HireDate"
        ]

        missing_fields = [
            field for field in required_fields
            if field not in data
        ]

        if missing_fields:
            return json_response(
                {
                    "error": "Missing required fields",
                    "fields": missing_fields
                },
                400
            )

        connection = get_connection()
        cursor = connection.cursor()

        # Check employee exists
        cursor.execute(
            """
            SELECT EmployeeID
            FROM Employee
            WHERE EmployeeID = ?
            """,
            employee_id
        )

        if cursor.fetchone() is None:
            connection.close()

            return json_response(
                {
                    "error": "Employee not found",
                    "EmployeeID": employee_id
                },
                404
            )

        # Check department exists
        cursor.execute(
            """
            SELECT DepartmentID
            FROM Department
            WHERE DepartmentID = ?
            """,
            data["DepartmentID"]
        )

        if cursor.fetchone() is None:
            connection.close()

            return json_response(
                {
                    "error": "Department does not exist",
                    "DepartmentID": data["DepartmentID"]
                },
                400
            )

        cursor.execute(
            """
            UPDATE Employee
            SET
                FirstName = ?,
                LastName = ?,
                DepartmentID = ?,
                Salary = ?,
                Bonus = ?,
                HireDate = ?
            WHERE EmployeeID = ?
            """,
            data["FirstName"],
            data["LastName"],
            data["DepartmentID"],
            data["Salary"],
            data.get("Bonus"),
            data["HireDate"],
            employee_id
        )

        connection.commit()
        connection.close()

        return json_response(
            {
                "message": "Employee updated successfully",
                "EmployeeID": employee_id
            }
        )

    except ValueError:
        return json_response(
            {"error": "EmployeeID must be an integer"},
            400
        )

    except Exception as e:
        return json_response(
            {
                "error": "Internal server error",
                "details": str(e)
            },
            500
        )


# ---------------------------------------------------------
# DELETE EMPLOYEE
# DELETE /api/employees/{employee_id}
# ---------------------------------------------------------

@app.route(route="employees/{employee_id}", methods=["DELETE"])
def delete_employee(req: func.HttpRequest) -> func.HttpResponse:

    try:
        employee_id = int(req.route_params.get("employee_id"))

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM Employee
            WHERE EmployeeID = ?
            """,
            employee_id
        )

        if cursor.rowcount == 0:
            connection.close()

            return json_response(
                {
                    "error": "Employee not found",
                    "EmployeeID": employee_id
                },
                404
            )

        connection.commit()
        connection.close()

        return func.HttpResponse(
            status_code=204
        )

    except ValueError:
        return json_response(
            {"error": "EmployeeID must be an integer"},
            400
        )

    except Exception as e:
        return json_response(
            {
                "error": "Internal server error",
                "details": str(e)
            },
            500
        )


# =========================================================
# REPORTS
# =========================================================


# ---------------------------------------------------------
# REPORT 1
# GET /api/reports/total-bonus
#
# Total company bonus.
# NULL bonuses are treated as zero.
# ---------------------------------------------------------

@app.route(route="reports/total-bonus", methods=["GET"])
def total_company_bonus(req: func.HttpRequest) -> func.HttpResponse:

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(Bonus), 0) AS TotalCompanyBonus
            FROM Employee
            """
        )

        row = cursor.fetchone()
        connection.close()

        return json_response(
            {
                "TotalCompanyBonus": float(row.TotalCompanyBonus)
            }
        )

    except Exception as e:
        return json_response(
            {
                "error": "Internal server error",
                "details": str(e)
            },
            500
        )


# ---------------------------------------------------------
# REPORT 2
# GET /api/reports/no-bonus
#
# Employees who have never received a bonus.
# ---------------------------------------------------------

@app.route(route="reports/no-bonus", methods=["GET"])
def employees_without_bonus(req: func.HttpRequest) -> func.HttpResponse:

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                EmployeeID,
                FirstName,
                LastName,
                DepartmentID,
                Salary,
                HireDate
            FROM Employee
            WHERE Bonus IS NULL
            ORDER BY EmployeeID
            """
        )

        rows = cursor.fetchall()
        connection.close()

        employees = []

        for row in rows:
            employees.append(
                {
                    "EmployeeID": row.EmployeeID,
                    "FirstName": row.FirstName,
                    "LastName": row.LastName,
                    "DepartmentID": row.DepartmentID,
                    "Salary": float(row.Salary),
                    "HireDate": row.HireDate.isoformat()
                }
            )

        return json_response(employees)

    except Exception as e:
        return json_response(
            {
                "error": "Internal server error",
                "details": str(e)
            },
            500
        )


# ---------------------------------------------------------
# REPORT 3
# GET /api/reports/bonus-percentages
#
# Each employee who has a bonus, along with bonus
# percentage of annual salary.
# ---------------------------------------------------------

@app.route(route="reports/bonus-percentages", methods=["GET"])
def employee_bonus_percentages(req: func.HttpRequest) -> func.HttpResponse:

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                EmployeeID,
                FirstName,
                LastName,
                Salary,
                Bonus,
                ROUND(
                    (Bonus / NULLIF(Salary, 0)) * 100,
                    2
                ) AS BonusPercentage
            FROM Employee
            WHERE Bonus IS NOT NULL
            ORDER BY EmployeeID
            """
        )

        rows = cursor.fetchall()
        connection.close()

        employees = []

        for row in rows:
            employees.append(
                {
                    "EmployeeID": row.EmployeeID,
                    "FirstName": row.FirstName,
                    "LastName": row.LastName,
                    "Salary": float(row.Salary),
                    "Bonus": float(row.Bonus),
                    "BonusPercentage": float(row.BonusPercentage)
                }
            )

        return json_response(employees)

    except Exception as e:
        return json_response(
            {
                "error": "Internal server error",
                "details": str(e)
            },
            500
        )


# ---------------------------------------------------------
# REPORT 4
# GET /api/reports/departments-above-average-salary
#
# Departments where total bonus > department average salary.
# ---------------------------------------------------------

@app.route(
    route="reports/departments-above-average-salary",
    methods=["GET"]
)
def departments_above_average_salary(req: func.HttpRequest) -> func.HttpResponse:

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                d.DepartmentID,
                d.DepartmentName,
                d.Location,
                COALESCE(SUM(e.Bonus), 0) AS TotalBonus,
                AVG(e.Salary) AS AverageSalary
            FROM Department d
            INNER JOIN Employee e
                ON d.DepartmentID = e.DepartmentID
            GROUP BY
                d.DepartmentID,
                d.DepartmentName,
                d.Location
            HAVING
                COALESCE(SUM(e.Bonus), 0) > AVG(e.Salary)
            ORDER BY
                TotalBonus DESC
            """
        )

        rows = cursor.fetchall()
        connection.close()

        departments = []

        for row in rows:
            departments.append(
                {
                    "DepartmentID": row.DepartmentID,
                    "DepartmentName": row.DepartmentName,
                    "Location": row.Location,
                    "TotalBonus": float(row.TotalBonus),
                    "AverageSalary": round(float(row.AverageSalary), 2)
                }
            )

        return json_response(departments)

    except Exception as e:
        return json_response(
            {
                "error": "Internal server error",
                "details": str(e)
            },
            500
        )


# ---------------------------------------------------------
# REPORT 5
# GET /api/reports/bonus-ranking
#
# Employees ranked by bonus amount.
# Employees with NULL bonus appear last.
# ---------------------------------------------------------

@app.route(route="reports/bonus-ranking", methods=["GET"])
def bonus_ranking(req: func.HttpRequest) -> func.HttpResponse:

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                EmployeeID,
                FirstName,
                LastName,
                DepartmentID,
                Salary,
                Bonus,
                RANK() OVER
                (
                    ORDER BY
                        CASE
                            WHEN Bonus IS NULL THEN 1
                            ELSE 0
                        END,
                        Bonus DESC
                ) AS BonusRank
            FROM Employee
            ORDER BY
                CASE
                    WHEN Bonus IS NULL THEN 1
                    ELSE 0
                END,
                Bonus DESC,
                EmployeeID
            """
        )

        rows = cursor.fetchall()
        connection.close()

        employees = []

        for row in rows:
            employees.append(
                {
                    "EmployeeID": row.EmployeeID,
                    "FirstName": row.FirstName,
                    "LastName": row.LastName,
                    "DepartmentID": row.DepartmentID,
                    "Salary": float(row.Salary),
                    "Bonus": (
                        float(row.Bonus)
                        if row.Bonus is not None
                        else None
                    ),
                    "BonusRank": row.BonusRank
                }
            )

        return json_response(employees)

    except Exception as e:
        return json_response(
            {
                "error": "Internal server error",
                "details": str(e)
            },
            500
        )


# ---------------------------------------------------------
# REPORT 6
# GET /api/reports/highest-salary
#
# Finds:
# 1. Employee with highest base salary
# 2. Employee with highest total compensation
# 3. Whether they are the same employee
#
# Total compensation = Salary + Bonus
# NULL bonus is treated as zero.
# ---------------------------------------------------------

@app.route(route="reports/highest-salary", methods=["GET"])
def highest_salary_report(req: func.HttpRequest) -> func.HttpResponse:

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Highest base salary
        cursor.execute(
            """
            SELECT TOP 1
                EmployeeID,
                FirstName,
                LastName,
                Salary,
                Bonus,
                Salary + COALESCE(Bonus, 0) AS TotalCompensation
            FROM Employee
            ORDER BY
                Salary DESC,
                EmployeeID ASC
            """
        )

        highest_salary_row = cursor.fetchone()

        # Highest total compensation
        cursor.execute(
            """
            SELECT TOP 1
                EmployeeID,
                FirstName,
                LastName,
                Salary,
                Bonus,
                Salary + COALESCE(Bonus, 0) AS TotalCompensation
            FROM Employee
            ORDER BY
                Salary + COALESCE(Bonus, 0) DESC,
                EmployeeID ASC
            """
        )

        highest_total_row = cursor.fetchone()

        connection.close()

        if highest_salary_row is None or highest_total_row is None:
            return json_response(
                {
                    "error": "No employees found"
                },
                404
            )

        highest_base_salary_employee = {
            "EmployeeID": highest_salary_row.EmployeeID,
            "FirstName": highest_salary_row.FirstName,
            "LastName": highest_salary_row.LastName,
            "Salary": float(highest_salary_row.Salary),
            "Bonus": (
                float(highest_salary_row.Bonus)
                if highest_salary_row.Bonus is not None
                else None
            ),
            "TotalCompensation": float(
                highest_salary_row.TotalCompensation
            )
        }

        highest_total_compensation_employee = {
            "EmployeeID": highest_total_row.EmployeeID,
            "FirstName": highest_total_row.FirstName,
            "LastName": highest_total_row.LastName,
            "Salary": float(highest_total_row.Salary),
            "Bonus": (
                float(highest_total_row.Bonus)
                if highest_total_row.Bonus is not None
                else None
            ),
            "TotalCompensation": float(
                highest_total_row.TotalCompensation
            )
        }

        same_employee = (
            highest_salary_row.EmployeeID
            == highest_total_row.EmployeeID
        )

        return json_response(
            {
                "highest_base_salary_employee":
                    highest_base_salary_employee,
                "highest_total_compensation_employee":
                    highest_total_compensation_employee,
                "same_employee":
                    same_employee
            }
        )

    except Exception as e:
        return json_response(
            {
                "error": "Internal server error",
                "details": str(e)
            },
            500
        )