select  p.firstname,p.lastname
from people p, directors d, credits c
where d.did =c.did and p.pid =d.did and c.aid = 

(

select pid 
from people 
where firstname ='Roger' and lastname ='Moore');



