# OVERVIEW: Azure Functions REST API in Python that does CRUD on an Employee table and 6 salary/bonus reports in SQL Server.

import os  # lets us read environment variables
import json  # lets us convert Python data to JSON text
import pyodbc  # library to connect Python to SQL Server
import azure.functions as func  # Azure Functions library (needed for routes, requests, responses)


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)  # creates the function app; ANONYMOUS = no API key needed


# ---------------------------------------------------------
# Database connection
# ---------------------------------------------------------

def get_connection():  # function that opens a database connection
    connection_string = os.getenv("SQL_CONNECTION_STRING")  # reads connection string from app settings

    if not connection_string:  # if the setting is missing or empty
        raise Exception("SQL_CONNECTION_STRING is not configured.")  # stop with a clear error message

    return pyodbc.connect(connection_string)  # connect to SQL Server and return the connection


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def employee_to_dict(row):  # converts one database row into a Python dictionary
    return {  # start returning the dictionary
        "EmployeeID": row.EmployeeID,  # employee id from the row
        "FirstName": row.FirstName,  # first name from the row
        "LastName": row.LastName,  # last name from the row
        "DepartmentID": row.DepartmentID,  # department id from the row
        "Salary": float(row.Salary),  # salary converted to float so JSON can handle it
        "Bonus": float(row.Bonus) if row.Bonus is not None else None,  # bonus as float, or None if no bonus
        "HireDate": row.HireDate.isoformat()  # date converted to text like 2024-01-31
    }  # end of dictionary


def json_response(data, status_code=200):  # helper to build a JSON HTTP response (default status 200 OK)
    return func.HttpResponse(  # create and return an HTTP response
        json.dumps(data, default=str),  # convert data to JSON text; unknown types become strings
        status_code=status_code,  # set the HTTP status code
        mimetype="application/json"  # tell client the response is JSON
    )  # end of response


# =========================================================
# EMPLOYEE CRUD
# =========================================================


# ---------------------------------------------------------
# CREATE EMPLOYEE
# POST /api/employees
# ---------------------------------------------------------

@app.route(route="employees", methods=["POST"])  # URL /api/employees for POST requests
def create_employee(req: func.HttpRequest) -> func.HttpResponse:  # function that creates a new employee

    try:  # start of error-handling block
        data = req.get_json()  # read the JSON body sent by the client

        required_fields = [  # list of fields that must be present
            "FirstName",  # first name is required
            "LastName",  # last name is required
            "DepartmentID",  # department id is required
            "Salary",  # salary is required
            "HireDate"  # hire date is required
        ]  # end of list

        missing_fields = [  # build list of missing fields
            field for field in required_fields  # loop over each required field
            if field not in data  # keep it only if it is not in the request data
        ]  # end of list

        if missing_fields:  # if anything is missing
            return json_response(  # send error response
                {  # error body start
                    "error": "Missing required fields",  # error message
                    "fields": missing_fields  # show which fields are missing
                },  # error body end
                400  # 400 = Bad Request
            )  # end of response

        first_name = data["FirstName"]  # get first name
        last_name = data["LastName"]  # get last name
        department_id = data["DepartmentID"]  # get department id
        salary = data["Salary"]  # get salary
        bonus = data.get("Bonus")  # get bonus (None if not given, it is optional)
        hire_date = data["HireDate"]  # get hire date

        connection = get_connection()  # open database connection
        cursor = connection.cursor()  # create cursor to run SQL commands

        # Check whether department exists
        cursor.execute(  # run a SQL query
            """
            SELECT DepartmentID  -- pick the department id column
            FROM Department  -- from the Department table
            WHERE DepartmentID = ParamHere  -- only the matching department
            """.replace("ParamHere", "?"),  # the placeholder is filled safely with the value below
            department_id  # value for the placeholder
        )  # end of execute

        if cursor.fetchone() is None:  # if no department row was found
            connection.close()  # close the connection

            return json_response(  # send error response
                {  # error body start
                    "error": "Department does not exist",  # error message
                    "DepartmentID": department_id  # show the wrong id
                },  # error body end
                400  # 400 = Bad Request
            )  # end of response

        cursor.execute(  # run the INSERT query
            """
            INSERT INTO Employee  -- add a new row to Employee table
            (
                FirstName,  -- column: first name
                LastName,  -- column: last name
                DepartmentID,  -- column: department id
                Salary,  -- column: salary
                Bonus,  -- column: bonus
                HireDate  -- column: hire date
            )
            OUTPUT INSERTED.EmployeeID  -- return the new auto-generated id
            VALUES (?, ?, ?, ?, ?, ?)  -- six placeholders for the six values
            """,  # end of SQL text
            first_name,  # value 1
            last_name,  # value 2
            department_id,  # value 3
            salary,  # value 4
            bonus,  # value 5
            hire_date  # value 6
        )  # end of execute

        employee_id = cursor.fetchone()[0]  # read the new employee id returned by OUTPUT

        connection.commit()  # save the insert permanently
        connection.close()  # close the connection

        return json_response(  # send success response
            {  # body start
                "message": "Employee created successfully",  # success message
                "EmployeeID": employee_id  # id of new employee
            },  # body end
            201  # 201 = Created
        )  # end of response

    except ValueError:  # happens when the JSON body is invalid
        return json_response(  # send error response
            {"error": "Invalid JSON request body"},  # error message
            400  # 400 = Bad Request
        )  # end of response

    except pyodbc.IntegrityError as e:  # database rule broken (foreign key, unique, etc.)
        return json_response(  # send error response
            {  # body start
                "error": "Database integrity error",  # error message
                "details": str(e)  # technical details of the error
            },  # body end
            400  # 400 = Bad Request
        )  # end of response

    except Exception as e:  # any other unexpected error
        return json_response(  # send error response
            {  # body start
                "error": "Internal server error",  # error message
                "details": str(e)  # technical details of the error
            },  # body end
            500  # 500 = Server Error
        )  # end of response


# ---------------------------------------------------------
# GET EMPLOYEE BY ID
# GET /api/employees/{employee_id}
# ---------------------------------------------------------

@app.route(route="employees/{employee_id}", methods=["GET"])  # URL /api/employees/5 for GET requests
def get_employee(req: func.HttpRequest) -> func.HttpResponse:  # function that fetches one employee

    try:  # start of error-handling block
        employee_id = int(req.route_params.get("employee_id"))  # take id from the URL and convert to integer

        connection = get_connection()  # open database connection
        cursor = connection.cursor()  # create cursor

        cursor.execute(  # run SELECT query
            """
            SELECT
                EmployeeID,  -- employee id
                FirstName,  -- first name
                LastName,  -- last name
                DepartmentID,  -- department id
                Salary,  -- salary
                Bonus,  -- bonus
                HireDate  -- hire date
            FROM Employee  -- from the Employee table
            WHERE EmployeeID = ?  -- only the requested employee
            """,  # end of SQL text
            employee_id  # value for the placeholder
        )  # end of execute

        row = cursor.fetchone()  # get the single matching row (or None)
        connection.close()  # close the connection

        if row is None:  # if no employee found
            return json_response(  # send not-found response
                {  # body start
                    "error": "Employee not found",  # error message
                    "EmployeeID": employee_id  # id that was searched
                },  # body end
                404  # 404 = Not Found
            )  # end of response

        return json_response(employee_to_dict(row))  # convert row to dict and send it (status 200)

    except ValueError:  # id in URL was not a number
        return json_response(  # send error response
            {"error": "EmployeeID must be an integer"},  # error message
            400  # 400 = Bad Request
        )  # end of response

    except Exception as e:  # any other unexpected error
        return json_response(  # send error response
            {  # body start
                "error": "Internal server error",  # error message
                "details": str(e)  # technical details
            },  # body end
            500  # 500 = Server Error
        )  # end of response


# ---------------------------------------------------------
# LIST EMPLOYEES
# GET /api/employees
# GET /api/employees?departmentId=1
# ---------------------------------------------------------

@app.route(route="employees", methods=["GET"])  # URL /api/employees for GET requests
def list_employees(req: func.HttpRequest) -> func.HttpResponse:  # function that lists employees

    try:  # start of error-handling block
        department_id = req.params.get("departmentId")  # optional filter from the query string

        connection = get_connection()  # open database connection
        cursor = connection.cursor()  # create cursor

        if department_id:  # if a department filter was given

            try:  # inner try to validate the number
                department_id = int(department_id)  # convert filter to integer
            except ValueError:  # if it is not a valid number
                connection.close()  # close the connection

                return json_response(  # send error response
                    {"error": "departmentId must be an integer"},  # error message
                    400  # 400 = Bad Request
                )  # end of response

            cursor.execute(  # run SELECT with department filter
                """
                SELECT
                    EmployeeID,  -- employee id
                    FirstName,  -- first name
                    LastName,  -- last name
                    DepartmentID,  -- department id
                    Salary,  -- salary
                    Bonus,  -- bonus
                    HireDate  -- hire date
                FROM Employee  -- from the Employee table
                WHERE DepartmentID = ?  -- only that department
                ORDER BY EmployeeID  -- sort by id
                """,  # end of SQL text
                department_id  # value for the placeholder
            )  # end of execute

        else:  # no filter given

            cursor.execute(  # run SELECT for all employees
                """
                SELECT
                    EmployeeID,  -- employee id
                    FirstName,  -- first name
                    LastName,  -- last name
                    DepartmentID,  -- department id
                    Salary,  -- salary
                    Bonus,  -- bonus
                    HireDate  -- hire date
                FROM Employee  -- from the Employee table
                ORDER BY EmployeeID  -- sort by id
                """
            )  # end of execute

        rows = cursor.fetchall()  # get all result rows
        connection.close()  # close the connection

        employees = [  # build list of dictionaries
            employee_to_dict(row)  # convert each row to a dictionary
            for row in rows  # loop through all rows
        ]  # end of list

        return json_response(employees)  # send the list as JSON

    except Exception as e:  # any unexpected error
        return json_response(  # send error response
            {  # body start
                "error": "Internal server error",  # error message
                "details": str(e)  # technical details
            },  # body end
            500  # 500 = Server Error
        )  # end of response


# ---------------------------------------------------------
# UPDATE EMPLOYEE
# PUT /api/employees/{employee_id}
# ---------------------------------------------------------

@app.route(route="employees/{employee_id}", methods=["PUT"])  # URL /api/employees/5 for PUT requests
def update_employee(req: func.HttpRequest) -> func.HttpResponse:  # function that updates an employee

    try:  # start of error-handling block
        employee_id = int(req.route_params.get("employee_id"))  # take id from URL as integer

        data = req.get_json()  # read the JSON body

        required_fields = [  # list of mandatory fields
            "FirstName",  # first name required
            "LastName",  # last name required
            "DepartmentID",  # department id required
            "Salary",  # salary required
            "HireDate"  # hire date required
        ]  # end of list

        missing_fields = [  # build list of missing fields
            field for field in required_fields  # loop over required fields
            if field not in data  # keep the ones not present in the body
        ]  # end of list

        if missing_fields:  # if any field is missing
            return json_response(  # send error response
                {  # body start
                    "error": "Missing required fields",  # error message
                    "fields": missing_fields  # list of missing fields
                },  # body end
                400  # 400 = Bad Request
            )  # end of response

        connection = get_connection()  # open database connection
        cursor = connection.cursor()  # create cursor

        # Check employee exists
        cursor.execute(  # run a SQL query
            """
            SELECT EmployeeID  -- pick the employee id column
            FROM Employee  -- from the Employee table
            WHERE EmployeeID = ?  -- only this employee
            """,  # end of SQL text
            employee_id  # value for the placeholder
        )  # end of execute

        if cursor.fetchone() is None:  # if employee not found
            connection.close()  # close the connection

            return json_response(  # send not-found response
                {  # body start
                    "error": "Employee not found",  # error message
                    "EmployeeID": employee_id  # id that was searched
                },  # body end
                404  # 404 = Not Found
            )  # end of response

        # Check department exists
        cursor.execute(  # run a SQL query
            """
            SELECT DepartmentID  -- pick the department id column
            FROM Department  -- from the Department table
            WHERE DepartmentID = ?  -- only the given department
            """,  # end of SQL text
            data["DepartmentID"]  # value for the placeholder
        )  # end of execute

        if cursor.fetchone() is None:  # if department not found
            connection.close()  # close the connection

            return json_response(  # send error response
                {  # body start
                    "error": "Department does not exist",  # error message
                    "DepartmentID": data["DepartmentID"]  # the wrong department id
                },  # body end
                400  # 400 = Bad Request
            )  # end of response

        cursor.execute(  # run the UPDATE query
            """
            UPDATE Employee  -- change existing row in Employee table
            SET
                FirstName = ?,  -- new first name
                LastName = ?,  -- new last name
                DepartmentID = ?,  -- new department id
                Salary = ?,  -- new salary
                Bonus = ?,  -- new bonus
                HireDate = ?  -- new hire date
            WHERE EmployeeID = ?  -- only update this employee
            """,  # end of SQL text
            data["FirstName"],  # value 1
            data["LastName"],  # value 2
            data["DepartmentID"],  # value 3
            data["Salary"],  # value 4
            data.get("Bonus"),  # value 5 (None if not given)
            data["HireDate"],  # value 6
            employee_id  # value 7 (for WHERE)
        )  # end of execute

        connection.commit()  # save the changes permanently
        connection.close()  # close the connection

        return json_response(  # send success response
            {  # body start
                "message": "Employee updated successfully",  # success message
                "EmployeeID": employee_id  # id of updated employee
            }  # body end
        )  # end of response

    except ValueError:  # id was not a number (or bad JSON)
        return json_response(  # send error response
            {"error": "EmployeeID must be an integer"},  # error message
            400  # 400 = Bad Request
        )  # end of response

    except Exception as e:  # any other unexpected error
        return json_response(  # send error response
            {  # body start
                "error": "Internal server error",  # error message
                "details": str(e)  # technical details
            },  # body end
            500  # 500 = Server Error
        )  # end of response


# ---------------------------------------------------------
# DELETE EMPLOYEE
# DELETE /api/employees/{employee_id}
# ---------------------------------------------------------

@app.route(route="employees/{employee_id}", methods=["DELETE"])  # URL /api/employees/5 for DELETE requests
def delete_employee(req: func.HttpRequest) -> func.HttpResponse:  # function that deletes an employee

    try:  # start of error-handling block
        employee_id = int(req.route_params.get("employee_id"))  # take id from URL as integer

        connection = get_connection()  # open database connection
        cursor = connection.cursor()  # create cursor

        cursor.execute(  # run the DELETE query
            """
            DELETE FROM Employee  -- remove a row from Employee table
            WHERE EmployeeID = ?  -- only this employee
            """,  # end of SQL text
            employee_id  # value for the placeholder
        )  # end of execute

        if cursor.rowcount == 0:  # if no row was deleted
            connection.close()  # close the connection

            return json_response(  # send not-found response
                {  # body start
                    "error": "Employee not found",  # error message
                    "EmployeeID": employee_id  # id that was searched
                },  # body end
                404  # 404 = Not Found
            )  # end of response

        connection.commit()  # save the delete permanently
        connection.close()  # close the connection

        return func.HttpResponse(  # send empty response
            status_code=204  # 204 = No Content (delete succeeded)
        )  # end of response

    except ValueError:  # id was not a number
        return json_response(  # send error response
            {"error": "EmployeeID must be an integer"},  # error message
            400  # 400 = Bad Request
        )  # end of response

    except Exception as e:  # any other unexpected error
        return json_response(  # send error response
            {  # body start
                "error": "Internal server error",  # error message
                "details": str(e)  # technical details
            },  # body end
            500  # 500 = Server Error
        )  # end of response


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

@app.route(route="reports/total-bonus", methods=["GET"])  # URL /api/reports/total-bonus for GET
def total_company_bonus(req: func.HttpRequest) -> func.HttpResponse:  # function that returns total bonus of company

    try:  # start of error-handling block
        connection = get_connection()  # open database connection
        cursor = connection.cursor()  # create cursor

        cursor.execute(  # run the SQL query
            """
            SELECT
                COALESCE(SUM(Bonus), 0) AS TotalCompanyBonus  -- add all bonuses; use 0 if result is NULL
            FROM Employee  -- from the Employee table
            """
        )  # end of execute

        row = cursor.fetchone()  # get the single result row
        connection.close()  # close the connection

        return json_response(  # send the result
            {  # body start
                "TotalCompanyBonus": float(row.TotalCompanyBonus)  # total bonus as float
            }  # body end
        )  # end of response

    except Exception as e:  # any unexpected error
        return json_response(  # send error response
            {  # body start
                "error": "Internal server error",  # error message
                "details": str(e)  # technical details
            },  # body end
            500  # 500 = Server Error
        )  # end of response


# ---------------------------------------------------------
# REPORT 2
# GET /api/reports/no-bonus
#
# Employees who have never received a bonus.
# ---------------------------------------------------------

@app.route(route="reports/no-bonus", methods=["GET"])  # URL /api/reports/no-bonus for GET
def employees_without_bonus(req: func.HttpRequest) -> func.HttpResponse:  # function listing employees without bonus

    try:  # start of error-handling block
        connection = get_connection()  # open database connection
        cursor = connection.cursor()  # create cursor

        cursor.execute(  # run the SQL query
            """
            SELECT
                EmployeeID,  -- employee id
                FirstName,  -- first name
                LastName,  -- last name
                DepartmentID,  -- department id
                Salary,  -- salary
                HireDate  -- hire date
            FROM Employee  -- from the Employee table
            WHERE Bonus IS NULL  -- only employees with no bonus
            ORDER BY EmployeeID  -- sort by id
            """
        )  # end of execute

        rows = cursor.fetchall()  # get all result rows
        connection.close()  # close the connection

        employees = []  # empty list to store results

        for row in rows:  # loop through each row
            employees.append(  # add one employee to the list
                {  # dictionary start
                    "EmployeeID": row.EmployeeID,  # employee id
                    "FirstName": row.FirstName,  # first name
                    "LastName": row.LastName,  # last name
                    "DepartmentID": row.DepartmentID,  # department id
                    "Salary": float(row.Salary),  # salary as float
                    "HireDate": row.HireDate.isoformat()  # date as text
                }  # dictionary end
            )  # end of append

        return json_response(employees)  # send the list as JSON

    except Exception as e:  # any unexpected error
        return json_response(  # send error response
            {  # body start
                "error": "Internal server error",  # error message
                "details": str(e)  # technical details
            },  # body end
            500  # 500 = Server Error
        )  # end of response


# ---------------------------------------------------------
# REPORT 3
# GET /api/reports/bonus-percentages
#
# Each employee who has a bonus, along with bonus
# percentage of annual salary.
# ---------------------------------------------------------

@app.route(route="reports/bonus-percentages", methods=["GET"])  # URL /api/reports/bonus-percentages for GET
def employee_bonus_percentages(req: func.HttpRequest) -> func.HttpResponse:  # function returning bonus percent of salary

    try:  # start of error-handling block
        connection = get_connection()  # open database connection
        cursor = connection.cursor()  # create cursor

        cursor.execute(  # run the SQL query
            """
            SELECT
                EmployeeID,  -- employee id
                FirstName,  -- first name
                LastName,  -- last name
                Salary,  -- salary
                Bonus,  -- bonus
                ROUND(  -- round the result
                    (Bonus / NULLIF(Salary, 0)) * 100,  -- bonus divided by salary times 100; NULLIF avoids divide by zero
                    2  -- keep 2 decimal places
                ) AS BonusPercentage  -- name of the calculated column
            FROM Employee  -- from the Employee table
            WHERE Bonus IS NOT NULL  -- only employees who have a bonus
            ORDER BY EmployeeID  -- sort by id
            """
        )  # end of execute

        rows = cursor.fetchall()  # get all result rows
        connection.close()  # close the connection

        employees = []  # empty list to store results

        for row in rows:  # loop through each row
            employees.append(  # add one employee to the list
                {  # dictionary start
                    "EmployeeID": row.EmployeeID,  # employee id
                    "FirstName": row.FirstName,  # first name
                    "LastName": row.LastName,  # last name
                    "Salary": float(row.Salary),  # salary as float
                    "Bonus": float(row.Bonus),  # bonus as float
                    "BonusPercentage": float(row.BonusPercentage)  # bonus percent as float
                }  # dictionary end
            )  # end of append

        return json_response(employees)  # send the list as JSON

    except Exception as e:  # any unexpected error
        return json_response(  # send error response
            {  # body start
                "error": "Internal server error",  # error message
                "details": str(e)  # technical details
            },  # body end
            500  # 500 = Server Error
        )  # end of response


# ---------------------------------------------------------
# REPORT 4
# GET /api/reports/departments-above-average-salary
#
# Departments where total bonus > department average salary.
# ---------------------------------------------------------

@app.route(  # start of route definition
    route="reports/departments-above-average-salary",  # URL path of this report
    methods=["GET"]  # only GET allowed
)  # end of route definition
def departments_above_average_salary(req: func.HttpRequest) -> func.HttpResponse:  # function for departments report

    try:  # start of error-handling block
        connection = get_connection()  # open database connection
        cursor = connection.cursor()  # create cursor

        cursor.execute(  # run the SQL query
            """
            SELECT
                d.DepartmentID,  -- department id
                d.DepartmentName,  -- department name
                d.Location,  -- department location
                COALESCE(SUM(e.Bonus), 0) AS TotalBonus,  -- total bonus of the department (NULL becomes 0)
                AVG(e.Salary) AS AverageSalary  -- average salary of the department
            FROM Department d  -- Department table with short name d
            INNER JOIN Employee e  -- join with Employee table (short name e)
                ON d.DepartmentID = e.DepartmentID  -- match employees to their department
            GROUP BY  -- group rows per department
                d.DepartmentID,  -- group by id
                d.DepartmentName,  -- group by name
                d.Location  -- group by location
            HAVING  -- filter the groups
                COALESCE(SUM(e.Bonus), 0) > AVG(e.Salary)  -- keep departments where total bonus is more than average salary
            ORDER BY  -- sort the result
                TotalBonus DESC  -- biggest total bonus first
            """
        )  # end of execute

        rows = cursor.fetchall()  # get all result rows
        connection.close()  # close the connection

        departments = []  # empty list to store results

        for row in rows:  # loop through each row
            departments.append(  # add one department to the list
                {  # dictionary start
                    "DepartmentID": row.DepartmentID,  # department id
                    "DepartmentName": row.DepartmentName,  # department name
                    "Location": row.Location,  # location
                    "TotalBonus": float(row.TotalBonus),  # total bonus as float
                    "AverageSalary": round(float(row.AverageSalary), 2)  # average salary rounded to 2 decimals
                }  # dictionary end
            )  # end of append

        return json_response(departments)  # send the list as JSON

    except Exception as e:  # any unexpected error
        return json_response(  # send error response
            {  # body start
                "error": "Internal server error",  # error message
                "details": str(e)  # technical details
            },  # body end
            500  # 500 = Server Error
        )  # end of response


# ---------------------------------------------------------
# REPORT 5
# GET /api/reports/bonus-ranking
#
# Employees ranked by bonus amount.
# Employees with NULL bonus appear last.
# ---------------------------------------------------------

@app.route(route="reports/bonus-ranking", methods=["GET"])  # URL /api/reports/bonus-ranking for GET
def bonus_ranking(req: func.HttpRequest) -> func.HttpResponse:  # function that ranks employees by bonus

    try:  # start of error-handling block
        connection = get_connection()  # open database connection
        cursor = connection.cursor()  # create cursor

        cursor.execute(  # run the SQL query
            """
            SELECT
                EmployeeID,  -- employee id
                FirstName,  -- first name
                LastName,  -- last name
                DepartmentID,  -- department id
                Salary,  -- salary
                Bonus,  -- bonus
                RANK() OVER  -- give a rank number to each row
                (
                    ORDER BY  -- ranking order
                        CASE  -- start condition
                            WHEN Bonus IS NULL THEN 1  -- no bonus gets 1 (goes last)
                            ELSE 0  -- has bonus gets 0 (goes first)
                        END,  -- end condition
                        Bonus DESC  -- then highest bonus first
                ) AS BonusRank  -- name of the rank column
            FROM Employee  -- from the Employee table
            ORDER BY  -- sort the final output
                CASE  -- start condition
                    WHEN Bonus IS NULL THEN 1  -- no bonus goes last
                    ELSE 0  -- has bonus goes first
                END,  -- end condition
                Bonus DESC,  -- highest bonus first
                EmployeeID  -- tie-breaker: lower id first
            """
        )  # end of execute

        rows = cursor.fetchall()  # get all result rows
        connection.close()  # close the connection

        employees = []  # empty list to store results

        for row in rows:  # loop through each row
            employees.append(  # add one employee to the list
                {  # dictionary start
                    "EmployeeID": row.EmployeeID,  # employee id
                    "FirstName": row.FirstName,  # first name
                    "LastName": row.LastName,  # last name
                    "DepartmentID": row.DepartmentID,  # department id
                    "Salary": float(row.Salary),  # salary as float
                    "Bonus": (  # bonus value start
                        float(row.Bonus)  # convert to float
                        if row.Bonus is not None  # only if bonus exists
                        else None  # otherwise keep None
                    ),  # bonus value end
                    "BonusRank": row.BonusRank  # rank number
                }  # dictionary end
            )  # end of append

        return json_response(employees)  # send the list as JSON

    except Exception as e:  # any unexpected error
        return json_response(  # send error response
            {  # body start
                "error": "Internal server error",  # error message
                "details": str(e)  # technical details
            },  # body end
            500  # 500 = Server Error
        )  # end of response


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

@app.route(route="reports/highest-salary", methods=["GET"])  # URL /api/reports/highest-salary for GET
def highest_salary_report(req: func.HttpRequest) -> func.HttpResponse:  # function for highest salary report

    try:  # start of error-handling block
        connection = get_connection()  # open database connection
        cursor = connection.cursor()  # create cursor

        # Highest base salary
        cursor.execute(  # run the SQL query
            """
            SELECT TOP 1  -- take only the first row
                EmployeeID,  -- employee id
                FirstName,  -- first name
                LastName,  -- last name
                Salary,  -- salary
                Bonus,  -- bonus
                Salary + COALESCE(Bonus, 0) AS TotalCompensation  -- salary plus bonus (NULL bonus is 0)
            FROM Employee  -- from the Employee table
            ORDER BY  -- sort the rows
                Salary DESC,  -- highest salary first
                EmployeeID ASC  -- tie-breaker: lower id first
            """
        )  # end of execute

        highest_salary_row = cursor.fetchone()  # store the top row (highest base salary)

        # Highest total compensation
        cursor.execute(  # run the second SQL query
            """
            SELECT TOP 1  -- take only the first row
                EmployeeID,  -- employee id
                FirstName,  -- first name
                LastName,  -- last name
                Salary,  -- salary
                Bonus,  -- bonus
                Salary + COALESCE(Bonus, 0) AS TotalCompensation  -- salary plus bonus (NULL bonus is 0)
            FROM Employee  -- from the Employee table
            ORDER BY  -- sort the rows
                Salary + COALESCE(Bonus, 0) DESC,  -- highest total compensation first
                EmployeeID ASC  -- tie-breaker: lower id first
            """
        )  # end of execute

        highest_total_row = cursor.fetchone()  # store the top row (highest total compensation)

        connection.close()  # close the connection

        if highest_salary_row is None or highest_total_row is None:  # if table is empty
            return json_response(  # send not-found response
                {  # body start
                    "error": "No employees found"  # error message
                },  # body end
                404  # 404 = Not Found
            )  # end of response

        highest_base_salary_employee = {  # dictionary for highest base salary employee
            "EmployeeID": highest_salary_row.EmployeeID,  # employee id
            "FirstName": highest_salary_row.FirstName,  # first name
            "LastName": highest_salary_row.LastName,  # last name
            "Salary": float(highest_salary_row.Salary),  # salary as float
            "Bonus": (  # bonus value start
                float(highest_salary_row.Bonus)  # convert to float
                if highest_salary_row.Bonus is not None  # only if bonus exists
                else None  # otherwise None
            ),  # bonus value end
            "TotalCompensation": float(  # total compensation as float
                highest_salary_row.TotalCompensation  # value from the row
            )  # end of float()
        }  # end of dictionary

        highest_total_compensation_employee = {  # dictionary for highest total compensation employee
            "EmployeeID": highest_total_row.EmployeeID,  # employee id
            "FirstName": highest_total_row.FirstName,  # first name
            "LastName": highest_total_row.LastName,  # last name
            "Salary": float(highest_total_row.Salary),  # salary as float
            "Bonus": (  # bonus value start
                float(highest_total_row.Bonus)  # convert to float
                if highest_total_row.Bonus is not None  # only if bonus exists
                else None  # otherwise None
            ),  # bonus value end
            "TotalCompensation": float(  # total compensation as float
                highest_total_row.TotalCompensation  # value from the row
            )  # end of float()
        }  # end of dictionary

        same_employee = (  # check if both are the same person
            highest_salary_row.EmployeeID  # id of highest salary employee
            == highest_total_row.EmployeeID  # compare with id of highest compensation employee
        )  # result is True or False

        return json_response(  # send the final result
            {  # body start
                "highest_base_salary_employee":  # key for first employee
                    highest_base_salary_employee,  # its value
                "highest_total_compensation_employee":  # key for second employee
                    highest_total_compensation_employee,  # its value
                "same_employee":  # key for the comparison result
                    same_employee  # True or False
            }  # body end
        )  # end of response

    except Exception as e:  # any unexpected error
        return json_response(  # send error response
            {  # body start
                "error": "Internal server error",  # error message
                "details": str(e)  # technical details
            },  # body end
            500  # 500 = Server Error
        )  # end of response