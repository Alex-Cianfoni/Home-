DROP VIEW ORDERLOG;
DROP VIEW BUILDCOST;
DROP VIEW CASECOST;
DROP VIEW MOTHERBOARDCOST;



DROP TABLE IF EXISTS Address;
DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS People;
DROP TABLE IF EXISTS Builds;
DROP TABLE IF EXISTS Motherboards;
DROP TABLE IF EXISTS OperatingSystems;
DROP TABLE IF EXISTS RAM;
DROP TABLE IF EXISTS Cases;

DROP TABLE IF EXISTS CPUs;
DROP TABLE IF EXISTS GraphicsCards;
DROP TABLE IF EXISTS StorageDevices;
DROP TABLE IF EXISTS Drive;
DROP TABLE IF EXISTS Powersupply;

DROP FUNCTION GPUSLOTTYPE;
DROP FUNCTION CPUMAKE;

--Address--
CREATE TABLE Address (
   aid         int not null,
   street      VARCHAR(100)not null,
   town        VARCHAR(50) not null,
   state       VARCHAR(10) not null,
   zip         VARCHAR(8)  not null,
 primary key(aid)

);
             
-- People --
CREATE TABLE People (
   pid         int not null,
   firstName   text,
   lastName    text,
   Address     int,
   Age         int,
 primary key(pid),
foreign key(address) references Address (aid),
	CONSTRAINT 	CHECK_AGE CHECK(age >= 18)
);


--CPU--
CREATE TABLE CPUs (
	cpuid int not null, 
    cpuname VARCHAR(100),
	make VARCHAR(10) not null,
    speed_GH FLOAT,
    sockettype VARCHAR(50),
    year INT,
    cost DECIMAL(10, 2) not null,
	primary key(cpuid),
	CONSTRAINT 	CHK_CPUCOST CHECK(cost > 0),
	CONSTRAINT  CHK_SPEED CHECK(speed_GH > 1)
);

-- Graphics Cards Table
CREATE TABLE GraphicsCards (
    gpuid int not null, 
    gpuname VARCHAR(100),
    make VARCHAR(50),
    memorysize INT,
    slottype VARCHAR(20) not null,
    year INT,
    cost DECIMAL(10, 2) not null,
	primary key  (gpuid),
	CONSTRAINT 	CHK_GPUCOST CHECK(cost > 0),
	CONSTRAINT  CHK_GPUMEM CHECK(memorysize >=1)
	
);

-- RAM Table
CREATE TABLE RAM (
	ramid int not null, 
    ramname VARCHAR(100),
    slottype VARCHAR(50),
    cost DECIMAL(10, 2) not null,
    brand VARCHAR(100),
    year INT,
	size_gb decimal(5,3), 
	primary key (ramid),
	CONSTRAINT 	CHK_RAMCOST CHECK(cost > 0)
);


-- Storage Devices Table
CREATE TABLE StorageDevices (
	storageid int not null,
    devicename VARCHAR(100),
    interfacetype VARCHAR(50),
    formfactor VARCHAR(10),
    cost DECIMAL(10, 2) not null,
    brand VARCHAR(100),
    speed VARCHAR(50),
	sizeTB int default 1 , 
	primary key (storageid),
	CONSTRAINT 	CHK_SIZE CHECK(sizeTB >= 1)
);

-- Motherboards Table
CREATE TABLE Motherboards (
	mid int not null,
    modelname VARCHAR(100),
    socket VARCHAR(50),
    cost DECIMAL(10, 2) not null,
    year INT,
	cpu int, 
	graphics int, 
	storage int, 
	primary key (mid),
	foreign key(cpu) references CPUs (cpuid),
	foreign key(graphics) references GraphicsCards (gpuid),
	foreign key(storage) references StorageDevices (storageid),
	CONSTRAINT 	CHK_MOTHERBOARDCOST CHECK(cost > 0),
	CONSTRAINT 	CHK_MAXCOST CHECK(cost < 1000)
	
);


-- Operating Systems Table
CREATE TABLE OperatingSystems (
	osid int not null,
    osname VARCHAR(100),
    year INT,
    cost DECIMAL(10, 2) not null,
    bittype int,
    make VARCHAR(100),
	primary key  (osid),
	CONSTRAINT 	CHK_OSCOST CHECK(cost > 0)
);
--Drive--
CREATE TABLE Drive (
	did int not null, 
	DriveType VARCHAR(20),
	Name VARCHAR(100),
	Speed VARCHAR(50),
	cost DECIMAL(10, 2) not null,
	Year INT,
	primary key (did),
	CONSTRAINT 	CHK_DRIVECOST CHECK(cost > 0)	
);
--PowerSupply--
CREATE TABLE PowerSupply(
	psid int not null,
    Name VARCHAR(50),
	Watt int, 
    cost DECIMAL(10, 2) not null,  
	primary key  (psid),
	CONSTRAINT 	CHK_POWERSUPPLYCOST CHECK(cost > 0),
	CONSTRAINT 	CHK_MINWATT CHECK(Watt > 200)
);


--Cases--
CREATE TABLE Cases (
	caseid int not null,
    Name VARCHAR(50),
    cost DECIMAL(10, 2) not null,
    FormFactor VARCHAR(20),
    Manufacturer VARCHAR(50),
    Year INT,
    Bays int default 1,
	powers int, 
	drives int, 
	primary key  (caseid),
	foreign key(powers) references PowerSupply (psid),
	foreign key(drives) references Drive (did),
	CONSTRAINT 	CHK_CASECOST CHECK(cost > 0),
	CONSTRAINT 	CHK_BaysCHECK CHECK(Bays >= 1)
);
--Builds--
CREATE TABLE Builds (
	bid int not null,
	motherboard int not null, 
	os int not null, 
	ram int not null, 
	cases int not null, 
	primary key (bid),
	foreign key(cases) references Cases (caseid),
	foreign key(motherboard) references Motherboards (mid),
	foreign key(os) references OperatingSystems (osid),
	foreign key(ram) references RAM (ramid)
	);


-- Orders --
CREATE TABLE Orders(
	pid int,
	bid int, 
	orderdate date, 
primary key(pid,bid),
foreign key(pid) references People (pid),
foreign key(bid) references Builds (bid)
	
);




-- SQL statements for loading example data
--Address--
INSERT INTO Address (aid,   street, town,     state, zip)
VALUES             (2001,  '123 st ',    'nowhere',  'va'    ,'7890'),
                   (2002,  '456 st ',    'elsewhere', 'nj'     , ' 5678'),
                   (2003,  '789 dr',   'somewhere',    'pa'   ,'1234'),
                   (2004,  '1011 lane', 'whereever',     'ny' ,' 6865')
             

-- People --
INSERT INTO People (pid,   firstName, lastName,     address, Age)
VALUES             (001,  'Alan',    'Labouseur',      2001,30),
                   (002,  'Alex',    'Cianfoni',       2002,20),
                   (003,  'Larry',   'Cianfoni',      2003 ,55),
                   (004,  'Sussane', 'Cianfoni',      2004,44)
             
			 

--CPU--
INSERT INTO CPUs (cpuid, cpuname, make, speed_GH, sockettype, year, cost)
VALUES
(701, 'Pentium 4','Intel', 2.0, ' 423', 2000, 150.00),
(702, 'Athlon XP 2500+','AMD', 1.833, ' 462', 2003, 90.00),
(703, 'Core 2 Duo E6600','Intel ', 2.4, 'LGA 775', 2006, 316.00),
(704, 'Phenom II X4 955 Black Edition','AMD', 3.2, ' AM3', 2009, 245.00),
(705, 'Core i7-2600K','Intel', 3.4, 'LGA 1155', 2011, 317.00),
(706, 'FX-8350','AMD', 4.0, 'AM3+', 2012, 199.00),
(707, 'Core i7-4770K','Intel', 3.5, 'LGA 1150', 2013, 339.00),
(708, 'Ryzen 5 3600X','AMD', 3.8, 'AM4', 2019, 249.00),
(709, 'Core i9-10900K','Intel', 3.7, 'LGA 1200', 2020, 488.00),
(710, 'Ryzen 7 5800X','AMD ', 3.8, 'AM4', 2020, 449.00);


--GraphicsCards--
INSERT INTO GraphicsCards (gpuid, gpuname, make, memorysize, slottype, year, cost)
VALUES               
(801, 'NVIDIA GeForce GTX 1650 Super', 'NVIDIA', 4, 'PCIe 3.0 x16', 2020, 159.00),
(802, 'AMD Radeon RX 5600 XT', 'AMD', 6, 'PCIe 4.0 x16', 2020, 279.00),
(803, 'NVIDIA GeForce RTX 2070 Super', 'NVIDIA', 8, 'PCIe 3.0 x16', 2019, 499.00),
(804, 'AMD Radeon RX 5700 XT', 'AMD', 8, 'PCIe 4.0 x16', 2019, 399.00),
(805, 'NVIDIA GeForce RTX 3080', 'NVIDIA', 10, 'PCIe 4.0 x16', 2020, 699.00),
(806, 'AMD Radeon RX 6800 XT', 'AMD', 16, 'PCIe 4.0 x16', 2020, 649.00),
(807, 'NVIDIA GeForce RTX 3090', 'NVIDIA', 24, 'PCIe 4.0 x16', 2020, 1499.00),
(808, 'AMD Radeon RX 6900 XT', 'AMD', 16, 'PCIe 4.0 x16', 2020, 999.00),
(809, 'NVIDIA GeForce GTX 1660 Super', 'NVIDIA', 6, 'PCIe 3.0 x16', 2019, 229.00),
(810, 'AMD Radeon RX 6700 XT', 'AMD', 12, 'PCIe 4.0 x16', 2021, 479.00);


--Ram--
INSERT INTO Ram (ramid, ramname, slottype, cost, brand, year,size_gb)
VALUES             
(401, '72-pin', '72-pin SIMM', 100.00, 'Various', 1990,0.016),
(402, 'DDR2', 'DDR2 DIMM', 40.00,  'Crucial', 2005,1),
(403, 'DDR3', 'DDR3 DIMM', 100.00, 'Crucial', 2010,8),
(404, 'DDR4', 'DDR4 DIMM', 150.00, 'Crucial', 2015,12),
(405, 'DDR4', 'DDR4 DIMM', 250.00, 'Corsair', 2018,32);

--StorageDevices--
INSERT INTO StorageDevices(storageid, devicename, interfacetype, formfactor, cost, brand, speed, sizeTB)
VALUES           
(901, 'HDD', 'SATA', '3.5"', 250.00, ' Western Digital', '125 MB/s',10),
(902, 'HDD', 'SATA', '3.5"', 175.00, ' Western Digital', '100 MB/s',8),
(903, 'HDD', 'SATA', '3.5"', 100.00, ' Western Digital', '99 MB/s',4),
(904, 'NVMe SSD', 'NVMe (M.2)', 'M.2', 250.00, 'Samsung ', '3000 MB/s',2),
(905, 'HDD', 'SATA', '3.5"', 65.00, 'Seagate ', '150 MB/s',2),
(906, 'NVMe SSD', 'NVMe (M.2)', 'M.2', 125.00, ' Crucial', '4000 MB/s',1);

--Motherboard--
INSERT INTO Motherboards(mid, modelname, socket, cost, year,cpu,graphics,storage)
VALUES              
(201, 'Gigabyte GA-EP45-DS4P Rev 1', 'LGA 775', 175.00, 2008,703,806,901),
(202, 'Asus Sabertooth 990FX R2.0', 'AM3+', 200.00, 2012,706,801,905),
(203, 'ASUS ROG Strix B450-F Gaming', 'AM4', 135.00, 2020,708,802,906),
(204, 'MSI MPG Z490 GAMING EDGE WIFI', 'LGA 1200', 225.00, 2020,709,804,902),
(205, 'ASRock B550 Phantom Gaming 4 AC', 'AM4', 135.00, 2020,710,807,904),
(206, 'Gigabyte B660 GAMING X AX DDR4 (Rev. 1.0)', 'LGA 1700', 175.00, 2022,709,807,905);


				  
				  
--OperatingSystems				  
INSERT INTO OperatingSystems(osid, osname, year, cost, bittype, make)
VALUES              
(301, 'MS-DOS', 1992, 70.00, 16, 'IBM'),
(302, 'Windows 95', 1994, 100.00, 16 ,'Microsoft'),
(303, 'Windows XP', 2001, 199.00, 64, 'Microsoft'),
(304, 'Windows 7', 2009, 159.00, 64, 'Microsoft'),
(305, 'Windows 8.1', 2013, 159.00, 64, 'Microsoft'),
(306, 'Windows 10', 2015, 139.00, 64, 'Microsoft');


--Drive
INSERT INTO Drive (did, DriveType, Name, Speed, Cost, Year) 
VALUES 
(1001,'Floppy', 'Teac FD-55GFR', '360 KBs', 50, 1985),
(1002,'Floppy', 'Teac FD-235HF', '1.44 MBs', 10,  2002),
(1003,'Floppy', 'NEC FD1231H', '1.44 MBs', 20,  2005),
(1004,'CD', 'Lite-On LTN-485', '48x', 30,  2002),
(1005,'CD/DVD', 'LG GH24NSC0B', '24x CD Read Write, 8x DVD Read Write', 20,  2015),
(1006,'CD/DVD', 'ASUS DRW-24B1ST', '24x CD Read Write, 8x DVD Read Write', 30,  2011),
(1007,'DVD', 'Lite-On LH-20A1S', '20x DVD Read', 30,  2008),
(1008,'DVD', 'Samsung SH-224BB', '24x DVD Read Write', 30,  2012),
(1009,'DVD', 'LG GH24NSB0', '24x DVD Read Write', 20,  2014);

--PowerSupply--
INSERT INTO PowerSupply (psid, name, Watt,  Cost) 
VALUES 
    (601,  'Seasonic S12III 250 ',250,  50),
    (602,  'Corsair CX450' ,450,  60),
    (603,   'EVGA SuperNOVA 750 G5', 750, 140),
    (604,  'Seasonic Prime TX-1000', 1000, 300);


--Case--
INSERT INTO Cases (caseid, Name, Cost, FormFactor, Manufacturer, Year, Bays, powers, drives) 
VALUES 
(501,'Fractal Design Define R6', 200, 'ATX', 'Fractal Design', 2017, 6,601,1001),
(502,'NZXT H510', 100, 'ATX', 'NZXT', 2019, 5,602,1002),
(503,'Corsair Obsidian 500D', 150, 'ATX', 'Corsair', 2018, 4,603,1003),
(504,'Phanteks Enthoo Evolv X', 250, 'ATX', 'Phanteks', 2018, 10,604,1001),
(505,'Cooler Master MasterCase H500P Mesh', 200, 'ATX', 'Cooler Master', 2017, 7,601,1005),
(506,'Lian Li PC-O11 Dynamic', 150, 'ATX', 'Lian Li', 2018, 6,601,1006),
(507,'be quiet! Dark Base Pro 900', 250, 'ATX', 'be quiet!', 2016, 7,602,1002),
(508,'Thermaltake Core P3', 150, 'Open Frame', 'Thermaltake', 2016, 4,603,1002),
(509,'NZXT Phantom 820', 250, 'E-ATX', 'NZXT', 2012, 8,601,1008),
(510,'Antec Nine Hundred', 150, 'ATX', 'Antec', 2007, 9,602,1009);


--Builds--
INSERT INTO Builds(bid, motherboard, os, ram,cases)
VALUES
(101,202,306,404,505),
(102,204,304,405,502),
(103,206,302,402,503),
(104,201,305,401,506),
(105,202,305,401,505),
(106,206,301,402,503),
(107,201,303,404,505),
(108,203,305,404,505);

--Orders--
INSERT INTO Orders(pid,bid,orderdate)
VALUES
(001,101,'2000-05-04'),
(002,102,'2001-06-04'),
(003,103,'2015-11-04'),
(004,104,'2020-08-14'),
(002,104,'2013-10-24'),
(001,102,'2016-12-04'),
(004,102,'2011-05-04'),
(003,104,'2019-06-15'),
(001,104,'2022-07-04'),
(002,103,'2024-03-02'),
(001,105,'2007-05-04'),
(002,106,'2002-06-04'),
(003,107,'2021-12-07'),
(004,108,'2021-01-14');








--views--

--This is the views showing the motherboard costs with a total cost--

CREATE OR REPLACE VIEW MOTHERBOARDCOST AS 
select m.mid, m.modelname, c.cpuname, g.gpuname, s.devicename, SUM(c.cost+ g.cost+s.cost+m.cost)AS TOTALCOST
from MotherBoards m ,CPUs c, GraphicsCards g , StorageDevices s
where m.cpu =c.cpuid and m.graphics =g.gpuid and m.storage =s.storageid
group by m.mid, m.modelname, c.cpuname, g.gpuname, s.devicename
order by m.mid;


--This view shows the case costs with a total cost--

CREATE OR REPLACE VIEW CASECOST AS 
select c.caseid,c.name as Cases ,p.name as Powersupply ,d.Name as Drive, SUM(c.cost+p.cost+d.cost)AS TOTALCOST
from Cases c , PowerSupply p, Drive d
where c.powers = p.psid and c.drives = d.did 
group by c.caseid,c.name,p.name ,d.Name
order by c.caseid 

--This view shows the build costs with a total cost--

CREATE OR REPLACE VIEW BUILDCOST AS 
select b.bid, M.modelname, o.osname,r.ramname, C.Cases as Casename, SUM(M.TOTALCOST+C.TOTALCOST+r.cost+o.cost) as TOTALSUMOFBUILD
from MOTHERBOARDCOST M, OperatingSystems o, Ram r, CASECOST C, Builds b 
where b.motherboard = M.mid and b.os = o.osid and b.ram = r.ramid and b.cases = C.caseid
group by b.bid, M.modelname, o.osname,r.ramname, C.Cases
order by b.bid;

--This views shows order log with a total cost--

CREATE OR REPLACE VIEW ORDERLOG AS 
select  p.firstname,p.lastname, b.modelname,b.osname,b.ramname,b.casename,o.orderdate,b.TOTALSUMOFBUILD
from People p, BUILDCOST b, Orders o 
where o.pid = p.pid and b.bid = o.bid
order by b.TOTALSUMOFBUILD;



---reports

-- biggest spender
select firstname,lastname, sum(TOTALSUMOFBUILD) as BIGGESTSPENDER
from ORDERLOG 
group by firstname,lastname
order by BIGGESTSPENDER DESC
limit 1;



--most popular case
select c.Name as Most_Popular_Case
from Cases c
where c.caseid = (
	select b.cases 
	from Builds b
	group by b.cases 
	limit 1
);

-- avg cost of a build 
select ROUND (AVG (TOTALSUMOFBUILD),2) AS AVG_BUILD_COST, Min (TOTALSUMOFBUILD) AS MIN_BUILD_COST , Max (TOTALSUMOFBUILD) AS MAX_BUILD_COST
from BUILDCOST

--end of reports 




-- stored procedures 
--finds people who bought stuff 
create or replace function PEOPLEITEMS(int, REFCURSOR) returns refcursor as 
$$
declare
  	person int       := $1;
   resultset   REFCURSOR := $2;
begin
   open resultset for 
      select o.*
      from ORDERLOG o , people p 
       where p.pid =person and p.firstname =o.firstname and p.lastname =o.lastname
	   order by o.orderdate;
   return resultset;
end;
$$ 
language plpgsql;

select PEOPLEITEMS(001, 'results1');
Fetch all from results1;



--finding socket compat 

create or replace function SOCKETSCOMPAT(int, REFCURSOR) returns refcursor as 
$$
declare
  	sockets int       := $1;
   resultset   REFCURSOR := $2;
begin
   open resultset for 
      select m.modelname as MOTHERBOARD,c.cpuname as COMPATCPU,m.socket as COMPATSOCKET
      from  Motherboards m, CPUs c
       where m.cpu =c.cpuid and m.socket = c.sockettype and m.mid = sockets;
   return resultset;
end;
$$ 
language plpgsql;

select SOCKETSCOMPAT(205, 'results2');
Fetch all from results2;



--finding powersupply and a drive that havent been picked 
create or replace function ISUSED(int,int, REFCURSOR) returns refcursor as 
$$
declare
  	power int       := $1;
	drive int       := $2;
	
   resultset   REFCURSOR := $3;
begin
   open resultset for 
      select c.name as CASENAME,p.name as POWERSUPPLYNAME,d.name as DRIVENAME,p.watt as POWERSUPPLYWATT,d.drivetype,d.speed AS DRIVESPEED,c.bays as CASEBAYS
      from PowerSupply p , Cases c,Drive d 
       where c.powers =p.psid and c.drives=d.did and c.powers = power and c.drives=drive;
   return resultset;
end;
$$ 
language plpgsql;

select ISUSED(602,1002, 'results3');
Fetch all from results3;


--sample it not working and showing nothing 
select ISUSED(601,1003, 'results4');
Fetch all from results4;



--triggers-- 



CREATE OR REPLACE FUNCTION GPUSLOTTYPE() RETURNS TRIGGER AS $$
BEGIN
IF new.slottype is NULL THEN
RAISE EXCEPTION 'slottype cant be null';
END IF;
IF (SELECT g.slottype
FROM GraphicsCards g
WHERE g.gpuid = new.gpuid) ='PCIe 2.0 x16' or 
(SELECT g.slottype
FROM GraphicsCards g
WHERE g.gpuid = new.gpuid) ='PCIe 1.0 x16'
THEN
RAISE EXCEPTION 'ERROR YOU CANNOT ENTER ANY GRAPHICS CARD WITH A SLOT TYPE BELLOW PCIE 3.0';
END IF;
RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER GPUSLOTTYPE
AFTER INSERT 
ON GraphicsCards 
FOR EACH ROW 
EXECUTE PROCEDURE GPUSLOTTYPE();




INSERT INTO GraphicsCards (gpuid, gpuname, make, memorysize, slottype, year, cost)
VALUES               
(815, 'NVIDIA GeForce GTX 1650 Super', 'NVIDIA', 4, 'PCIe 1.0 x16', 2020, 159.00);




CREATE OR REPLACE FUNCTION CPUMAKE() RETURNS TRIGGER AS $$
BEGIN
IF new.make is NULL THEN
RAISE EXCEPTION 'make cant be null';
END IF;
IF (SELECT c.make
FROM CPUs c
WHERE c.cpuid = new.cpuid) NOT in ('Intel','AMD')
THEN
RAISE EXCEPTION 'MUST BE INTEL OR AMD';
END IF;
RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER CPUMAKE
AFTER INSERT 
ON CPUS 
FOR EACH ROW 
EXECUTE PROCEDURE CPUMAKE();

INSERT INTO CPUs (cpuid, cpuname, make, speed_GH, sockettype, year, cost)
VALUES
(711, 'Pentium 4','CYRIX', 2.0, ' 423', 2000, 150.00);



















--Security 

CREATE ROLE Admin;
GRANT ALL ON ALL TABLES
IN SCHEMA PUBLIC
TO Admin;

CREATE ROLE Manager;
GRANT Update, Select, Insert, Delete on all tables
IN SCHEMA PUBLIC
TO Manager;



CREATE ROLE Employee;
GRANT select ON all TABLES IN SCHEMA PUBLIC
TO Employee;


GRANT Update, Select, Insert ON builds
TO Employee;














-- SQL statements for displaying this example data:
select *
from Address;

select *
from People;

select *
from CPUs;

select *
from Motherboards;

select *
from GraphicsCards;

select *
from OperatingSystems;

select *
from MOTHERBOARDCOST;

select *
from CASECOST;

select *
from BUILDCOST;

select *
from ORDERLOG;

select *
from Builds;

select *
from Orders;

select *
from PowerSupply;

select *
from StorageDevices;

select *
from Ram;

select *
from Drive;

select *
from Cases;






