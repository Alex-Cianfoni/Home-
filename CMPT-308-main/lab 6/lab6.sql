/*
1. Display the cities that makes the most different kinds of products. Experiment with the rank() function.
2. Display the names of products whose priceUSD is less than 1% of the average priceUSD, in alphabetical order. from A to Z.
3. Display the customer last name, product id ordered, and the totalUSD for all orders made in March of any year, sorted by totalUSD from low to high.
4. Display the last name of all customers (in reverse alphabetical order) and their total ordered by customer, and nothing more. Use coalesce to avoid showing NULL totals.
5. Display the names of all customers who bought products from agents based in Chilliwack along with the names of the products they ordered, and the names of the agents who sold it to them.
6. Write a query to check the accuracy of the totalUSD column in the Orders table. This means calculating Orders.totalUSD from data in other tables and comparing those values to the values in Orders.totalUSD. Display all rows in Orders where Orders.totalUSD is incorrect, if any. If there are any incorrect values, explain why they are wrong. Round to exactly two decimal places.
7. Display the ;irst and last name of all customers who are also agents.
8. Create a VIEW of all Customer and People data called PeopleCustomers. Then another VIEW of all Agent and People data called PeopleAgents. Then select * from each of them to test them.
9. Display the ;irst and last name of all customers who are also agents, this time using the views you created.
10. Compare your SQL in #7 (no views) and #9 (using views). The output is the same. How does that work? What is the database server doing internally when it processes the #9 query?
11. [Bonus] What’s the difference between a LEFT OUTER JOIN and a RIGHT OUTER JOIN? Give example queries in SQL to demonstrate. (Feel free to use the CAP database to make your points here.)
*/











--1. Display the cities that makes the most different kinds of products. Experiment with the rank() function.

select city
from products 
group by city 
order by count (prodId)DESC 
limit 1




--chat 
SELECT 
    city,
    COUNT(DISTINCT prodId) AS num_products
FROM 
    Products
GROUP BY 
    city
ORDER BY 
    COUNT(DISTINCT prodId) DESC
LIMIT 1;







--2. Display the names of products whose priceUSD is less than 1% of the average priceUSD, in alphabetical order. from A to Z.
select name 
from  products 
where priceUSD <(select AVG(priceUSD) *0.01
				 from products )
				 ORDER BY 
    name ASC;





--
SELECT 
    name
FROM 
    Products
WHERE 
    priceUSD < (SELECT AVG(priceUSD) * 0.01 FROM Products)
ORDER BY 
    name ASC;







--3. Display the customer last name, product id ordered, and the totalUSD for all orders made in March of any year, sorted by totalUSD from low to high.

select distinct p.lastName, n.prodID, o.totalUSD
from orders o ,products n , people p, customers c
where n.prodID = o.prodID and o.custID = c.pid and c.pid =p.pid
and date_part('month',dateOrdered) = 3
order by o.totalUSD 



SELECT 
    p.lastName AS customer_last_name,
    o.prodId AS product_id_ordered,
    o.totalUSD
FROM 
    Orders o
JOIN 
    Customers c ON o.custId = c.pid
JOIN 
    People p ON c.pid = p.pid
WHERE 
    EXTRACT(MONTH FROM o.dateOrdered) = 3
ORDER BY 
    o.totalUSD;






--4. Display the last name of all customers (in reverse alphabetical order) and their total ordered by customer, and nothing more. 
--Use coalesce to avoid showing NULL totals.

select p.lastName ,Coalesce (sum (totalUSD) ,0) as total
from Customers c left outer join people p on p.pid = c.pid
     left outer join Orders o on o.custID = c.pid
	 group by o.custID, p.lastname
order by p.lastName DESC

	

--chat 

SELECT 
    p.lastName AS customer_last_name,
    COALESCE(SUM(o.totalUSD), 0) AS total_ordered
FROM 
    People p
LEFT JOIN 
    Customers c ON p.pid = c.pid
LEFT JOIN 
    Orders o ON c.pid = o.custId
GROUP BY 
    p.lastName
ORDER BY 
    p.lastName DESC;
	
	
	
	SELECT 
    p.lastName AS customer_last_name,
    COALESCE(SUM(o.totalUSD), 0) AS total_ordered
FROM 
    Customers c
LEFT JOIN 
    Orders o ON c.pid = o.custId
LEFT JOIN 
    People p ON c.pid = p.pid
GROUP BY 
    p.lastName
ORDER BY 
    p.lastName DESC;









--5. Display the names of all customers who bought products from agents based in Chilliwack along with the names of the products they ordered,
-- and the names of the agents who sold it to them.


select distinct p1.firstName, p1.lastName,n.name, p2.firstName, p2.lastName
from people p1, people p2, agents a, customers c, products n, orders o 
where p1.pid = c.pid and c.pid =o.custID and a.pid =o.agentID and p2.pid= a.pid and p2.homecity ='Chilliwack' and o.prodID =n.prodID
and o.agentID in(
select a.pid 
from agents a, people p 
where p.pid =a.pid and p.homeCity ='Chilliwack'
)



--
SELECT 
    p.lastName AS customer_name,
    pr.name AS product_name,
    a.firstName || ' ' || a.lastName AS agent_name
FROM 
    Orders o
JOIN 
    Customers c ON o.custId = c.pid
JOIN 
    People p ON c.pid = p.pid
JOIN 
    Products pr ON o.prodId = pr.prodId
JOIN 
    Agents ag ON o.agentId = ag.pid
JOIN 
    People a ON ag.pid = a.pid
WHERE 
    a.homeCity = 'Chilliwack';







--6. Write a query to check the accuracy of the totalUSD column in the Orders table. 
--This means calculating Orders.totalUSD from data in other tables and comparing those values to the values in Orders.totalUSD.
--Display all rows in Orders where Orders.totalUSD is incorrect, if any. If there are any incorrect values, explain why they are wrong. 
--Round to exactly two decimal places.

select o.orderNum, round (sum (o.quantityOrdered * p.priceUSD / (1+ c.discountPct/100)) ,2) as finalcalc, o.totalUSD
from products p, orders o , customers c 
where p.prodId =o.prodID and c.pid =o.custID
group by o.totalUSD, o.orderNum
having sum (o.quantityOrdered * p.priceUSD / (1 + c.discountPct/100)) != o.totalUSD
order by o.orderNum




---
SELECT 
    o.*,
    ROUND(SUM(pr.priceUSD * o.quantityOrdered), 2) AS calculated_total
FROM 
    Orders o
JOIN 
    Products pr ON o.prodId = pr.prodId
GROUP BY 
    o.orderNum
HAVING 
    ROUND(SUM(pr.priceUSD * o.quantityOrdered), 2) != o.totalUSD;



--there are all wrong becuause the there is a small margin of error in the finalcalc and the total usd. 

--7. Display the first and last name of all customers who are also agents.
select distinct p.firstName, p.lastname
from people p , customers c, agents a 
where p.pid = c.pid and p.pid = a.pid


--

SELECT 
    c.firstName AS first_name,
    c.lastName AS last_name
FROM 
    People c
JOIN 
    Customers cu ON c.pid = cu.pid
JOIN 
    Agents a ON c.pid = a.pid;



--8. Create a VIEW of all Customer and People data called PeopleCustomers. Then another VIEW of all Agent and People data called PeopleAgents. 
--Then select * from each of them to test them.

create view PeopleCustomers  as
select p.*,c.paymentTerms,c.discountPct
from customers c,people p
where c.pid =p.pid 

select *
from PeopleCustomers 

create view PeopleAgents as
select p.*,a.paymentTerms,a.commissionPct
from agents a,people p
where a.pid =p.pid 

select *
from  PeopleAgents





--9. Display the first and last name of all customers who are also agents, this time using the views you created.

select  a.firstName, a.lastname
from PeopleCustomers c,  PeopleAgents a 
where c.pid = a.pid 





--10. Compare your SQL in #7 (no views) and #9 (using views). The output is the same. 
--How does that work? What is the database server doing internally when it processes the #9 query?



--It works becusae it creates a copy of the answer table so that you can take information from the said table. It accesses the views and seees the answer table. 




--11. [Bonus] What’s the difference between a LEFT OUTER JOIN and a RIGHT OUTER JOIN? Give example queries in SQL to demonstrate. (Feel free to use the CAP database to make your points here.)

-- it would take everything from the left table and any that matches in the right table. if there are unmatched values in the left table then it becomes null in the right, 

-- it would take everything from the right and any that matches in the left table. if there are unmatched values in the right table then it becomes null in the left

--ex 

select *
from people p 
left join customers c on p.pid =c.pid 

select *
from people p 
right join customers c on p.pid =c.pid 


select *
from  customers c 
right join people p on p.pid =c.pid 