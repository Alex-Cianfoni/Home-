/*1. Show all the People data (and only people data) for people who are customers. Use joins this time; no subqueries.
2. Show all the People data (and only the people data) for people who are agents. Use joins this time; no subqueries.
3. Show all People and Agent data for people who are both customers and agents. Use joins this time; no subqueries.
4. Show the first name of customers who have never placed an order. Use subqueries.
5. Show the first name of customers who have never placed an order. Use one inner and one outer join.
6. Show the id and commission percent of Agents who booked an order for the Customer whose id is 008, sorted by commission percent from high to low. Use joins; no subqueries.
7. Show the last name, home city, and commission percent of Agents who booked an order for the customer whose id is 001, sorted by commission percent from high to low. Use joins.
8. Show the last name and home city of customers who live in the city that makes the fewest different kinds of products. (Hint: Use count and group by on the Products table. You may need limit as well.)
9. Show the name and id of all Products ordered through any Agent who booked at least one order for a Customer in Arlington, sorted by product name from A to Z. You can use joins or subqueries. Better yet, impress me by doing it both ways.
10. Show the Rirst and last name of customers and agents living in the same city, along with the name of their shared city. (Living in a city with yourself does not count, so exclude those from your results.
*/






-- 1. Show all the People data (and only people data) for people who are Customers.
--    Use joins this time; no subqueries.
select p.*
from People p inner join Customers c on p.pid = c.pid;


-- 2. Show all the People data (and only the people data) for people who are Agents.
--    Use joins this time; no subqueries.
select p.*
from People p inner join Agents a on p.pid = a.pid;



--3. Show all People and Agent data for people who are both customers and agents. Use joins this time; no subqueries.

-- just a working prototype 

select p.*
from People p inner join Agents    a on p.pid = a.pid
              inner join Customers c on p.pid = c.pid;
			  

			  
			  
--4. Show the first name of customers who have never placed an order. Use subqueries.
--
select p.firstName
from people p ,customers c 
where p.pid =c.pid and c.pid not in (
select o.custID 
from orders o 
)


--5. Show the first name of customers who have never placed an order. Use one inner and one outer join.



select p.firstName
from People p inner join Customers c on p.pid = c.pid
         	left outer join Orders o on o.custId = c.pid
			where o.custId is null

					

			 
			 
		
			 
--6. Show the id and commission percent of Agents who booked an order for the Customer whose id is 008, 
--sorted by commission percent from high to low. Use joins; no subqueries.
	
select  a.pid, a.commissionPct
from Agents a inner join Orders o on a.pid = o.agentID 
where o.custId = 8
order by a.commissionPct DESC
	  
			


--7. Show the last name, home city, and commission percent of Agents who booked an order for the customer whose id is 001, 
--sorted by commission percent from high to low. Use joins.



				
select  distinct a.commissionPct , p.lastName, p.homeCity
from Agents a inner join Orders o on a.pid = o.agentID
			  inner join People p on p.pid = a.pid 
where o.custId = 1
order by a.commissionPct DESC

			

--8. Show the last name and home city of customers who live in the city that makes the fewest different kinds of products. 
--(Hint: Use count and group by on the Products table. You may need limit as well.)



select p.lastName, p.homeCity
from People p
where p.homeCity in (
select city
from products 
group by city 
order by count (prodId)ASC 
limit 1)




			








--9. Show the name and id of all Products ordered through any Agent who booked at least one order for a Customer in Arlington, sorted by product name from A to Z. 
--You can use joins or subqueries. Better yet, impress me by doing it both ways.

select p.name,p.prodID
from products p  
where p.prodID in (
	
select o1.prodID
	from orders o1
	where o1.agentID in (
	
		select o2.agentId 
		from orders o2 
		where
o2.custID in(
select customers.pid
from customers, people 
where customers.pid= people.pid
and people.homeCity ='Arlington')))
order by p.name ASC



	
	
	
	




--10. Show the first and last name of customers and agents living in the same city, along with the name of their shared city. 
--(Living in a city with yourself does not count, so exclude those from your results.


select p1.firstName, p1.lastName, p2.firstName, p2.lastName, p1.homeCity
from customers c , agents a ,people p1, people p2
where p1.pid = c.pid and p2.pid = a.pid and p1.homeCity =p2.homeCity and p1.pid != p2.pid







