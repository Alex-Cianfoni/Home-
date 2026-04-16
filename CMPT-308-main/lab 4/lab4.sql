/*select (DOB> current_date -interval '50 years')

select Pid
from people 
--union All  INTERSECT --
EXCEPT
select Pid
from customers 
order by Pid ASC; 

1. Get all the People data for people who are customers.
2. Get all the People data for people who are agents.
3. Get all of People data for people who are both customers and agents.
4. Get all of People data for people who are neither customers nor agents.
5. Get the ID of customers who ordered either product p01 or p03 (or both). List the IDs in order from lowest to highest. Include each ID only once.
6. Get the ID of customers who ordered both products p01 and p03. List the IDs in order from highest to lowest. Include each ID only once.
7. Get the ]irst and last names of agents who sold products p05 or p07 in order by last name from A to Z.
8. Get the home city and birthday of agents booking an order for the customer whose pid is 008, sorted by home city from Z to A.
9. Get the unique ids of products ordered through any agent who takes at least one order from a customer in Montreal, sorted by id from highest to lowest. (This is not the same as asking for ids of products ordered by customers in Montreal.)
10. Get the last name and home city for all customers who place orders through agents in Chilliwack or Oslo in order by last name from A to Z.

*/ 

--1 Get all the People data for people who are customers.


select *
from people 
where Pid in (select Pid
		from people 
 			INTERSECT 
				select Pid
					from customers);
		

--2 Get all the People data for people who are agents.

select *
from people 
where Pid in (select Pid
		from people 
 			INTERSECT 
				select Pid
					from Agents);
				

		


--3  Get all of People data for people who are both customers and agents.

select *
from people 
where Pid in (select Pid
		from people 
 			INTERSECT 
				select Pid
					from customers 
					where Pid in (select Pid
		from people 
 			INTERSECT 
				select Pid
					from Agents));
				
				
					
					
				
					
--4 Get all of People data for people who are neither customers nor agents.
						
select *
from people 
where Pid  Not in (select Pid
		from people 
 			INTERSECT 
				select Pid
					from customers 
					where Pid Not in (select Pid
		from people 
 			INTERSECT 
				select Pid
					from Agents));
					
					
					
-- 5 Get the ID of customers who ordered either product p01 or p03 (or both). List the IDs in order from lowest to highest. Include each ID only once.


									 
									 
select *
from orders
where custid in ( select custId
               from Orders
               where prodId = 'p01'
                  or prodId = 'p03' )
order by custid ASC;
									 
							

-- 6. Get the ID of customers who ordered both products p01 and p03. List the IDs in order from highest to lowest. Include each ID only once.


select custid
from orders
where custid in ( select custId
               from Orders
               where prodId = 'p01'
                  or prodId = 'p03' )
order by custid ASC;

									 
									 
									 
--7. Get the first and last names of agents who sold products p05 or p07 in order by last name from A to Z.		

select firstName, lastName
from People
where pid in ( select agentId
               from Orders
               where prodId = 'p05'
                  or prodId = 'p07' )
order by lastName ASC;








						
													
													
--  8. Get the home city and birthday of agents booking an order for the customer whose pid is 008, sorted by home city from Z to A.



select *
from orders
where agentid in ( select agentId
               from Orders
               where agentid = '5'
				   )
order by agentid DESC;

--9 Get the unique ids of products ordered through any agent who takes at least one order from a customer in Montreal, sorted by id from highest to lowest. (This is not the same as asking for ids of products ordered by customers in Montreal.)


select distinct prodid
from orders, people 
where homecity = 'Montreal' and custid ='1' or custid ='10'
order by prodid DESC;




--10. Get the last name and home city for all customers who place orders through agents in Chilliwack or Oslo in order by last name from A to Z.


select  lastName, homecity 
from orders, people 
where homecity = 'Chilliwack' or homecity = 'Oslo' 
order by prodid ASC;



select distinct p.lastName, p.homecity
from orders o, people p
where homecity = 'Chilliwack' 
order by o.prodid ASC;











