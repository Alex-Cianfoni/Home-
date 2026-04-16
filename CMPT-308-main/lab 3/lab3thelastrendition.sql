--1 /*List the order number and total dollars of all orders.*/
select orderNum, totalUSD
from Orders


--2 /*List the last name and home city of people whose prefix is “Ms.”.*/
select lastName, homeCity
from people
where prefix = 'Ms.'

	


--3 /*List id, name, and quantity on hand of products with quantity more than 1007.*/
select prodid, name, qtyOnHand
from Products
where qtyOnHand >'1007'



--4 /*List the first name and home city of people born in the 1920s.*/
select * -- firstName, homeCity, DOB
from people 
where DOB <= '1929-12-31' and DOB >'1920-01-01';



--5 /*List the prefix and last name of people who are not “Mr.”.*/
select prefix, lastName
from people
where prefix !='Mr.';



--6 /*List all fields for products in neither Dallas nor Duluth that cost US$17 or less.*/
select city, priceUSD
from products, orders 
where priceUSD <= '17' and city != 'Dallas' and city != 'Duluth'


--7 /*List all fields for orders in January of any year.*/

select *, extract (month from dateOrdered)
from orders
where date_part('month',dateOrdered) = 1




--8 /*List all fields for orders in February of any year of US$23,000 or more.*/

select * ,extract (month from dateOrdered)
from orders
where date_part('month',dateOrdered) = 2
and totalUSD >= '23000.0'


--9 /*List all orders from the customer whose id is 007*/

select * 
from people, orders 
where custID = 007;


--10 /*List all orders from the customer whose id is 00*/
select * 
from people, orders 
where custID = 005;



-- all 

select *
from people,customers, agents, products, orders 
where prefix = 'Ms.' 
and qtyOnHand >'1007' 
and DOB <= '1929-12-31' and DOB >'1920-01-01' 
and prefix !='Mr.'
and priceUSD <= '17.00' and city != 'Dallas' and city != 'Duluth'
and extract (month from dateOrdered) = 1
and totalUSD >=23000  
and custID =007
or custID =005;



