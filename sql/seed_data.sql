-- Employee Compensation Service
-- Seed data

-- Departments
INSERT INTO Department
(
    DepartmentID,
    DepartmentName,
    Location
)
VALUES
(1, 'Engineering', 'Pune'),
(2, 'Finance', 'Mumbai'),
(3, 'HR', 'Pune'),
(4, 'Sales', 'Bengaluru');


-- Employees
INSERT INTO Employee
(
    FirstName,
    LastName,
    DepartmentID,
    Salary,
    Bonus,
    HireDate
)
VALUES
('Aarav', 'Sharma', 1, 850000.00, 100000.00, '2024-01-15'),
('Priya', 'Mehta', 1, 950000.00, NULL,       '2023-06-10'),
('Rohan', 'Patil', 2, 700000.00, 50000.00,  '2022-11-20'),
('Sneha', 'Kulkarni', 2, 800000.00, NULL,   '2024-03-01'),
('Amit', 'Joshi', 3, 600000.00, 30000.00,   '2021-08-12'),
('Neha', 'Deshmukh', 4, 1100000.00, 150000.00, '2020-05-05'),
('Vikram', 'Shah', 4, 1200000.00, NULL,     '2019-09-18');
