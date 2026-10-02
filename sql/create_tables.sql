-- Employee Compensation Service
-- Database schema

CREATE TABLE Department (
    DepartmentID INT NOT NULL PRIMARY KEY,
    DepartmentName VARCHAR(100) NOT NULL,
    Location VARCHAR(100) NULL
);

CREATE TABLE Employee (
    EmployeeID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    DepartmentID INT NOT NULL,
    Salary DECIMAL(12,2) NOT NULL,
    Bonus DECIMAL(12,2) NULL,
    HireDate DATE NOT NULL,

    CONSTRAINT FK_Employee_Department
        FOREIGN KEY (DepartmentID)
        REFERENCES Department(DepartmentID)
);

-- Indexes to support common queries
CREATE INDEX IX_Employee_DepartmentID
ON Employee(DepartmentID);

CREATE INDEX IX_Employee_Bonus
ON Employee(Bonus);
