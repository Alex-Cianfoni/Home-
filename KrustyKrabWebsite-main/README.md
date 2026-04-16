Welcome to the Krusty Krab Restaurant Website
This folder contains all the files needed to run the Krusty Krab Website and Reservation System. Follow the instructions below to set up and use the system.



Folder Contents

HTML Files:
HomePage.html: The main page for the website.
AboutPage.html: The about page with restaurant information.
ContactPage.html: The contact page for inquiries.
MenuPage.html: The menu page listing the food items.

CSS File:
KrustyKrab.css

JavaScript Files:
KrustyKrab.js: Client-side functionality, including reservation search and availability checks.
server.js: Server-side functionality to fetch reservation data from Google Sheets.

Other Files:
package.json: Node.js project file for managing dependencies.



Prerequisites
Before starting, ensure the following are installed on your computer:

Node.js (includes npm): Download from Node.js Official Website.



Setup Instructions


Step 1: Install Node.js Dependencies
Open a terminal/command prompt.
Navigate to the folder containing these files. 
For example:"cd /path/to/this/folder"

Install required packages:
npm install

This will install:
express: A lightweight web server.
axios: HTTP client for fetching reservation data.
cors: Middleware to handle cross-origin requests.


Step 2: Start the Server
Run the following command to start the server:"npm start"

This will start the server on http://localhost:3000

Step 3: Open the Website
Open the HomePage.html file in your browser



Using the "Web"site

Main Features:

View all reservations directly from the homepage.
Search for reservations by date using the search bar.
Check availability for a specific date and time using the reservation form.

Pages:

Home: Displays reservations and allows search/availability checks.
About: General restaurant information.
Contact: Contact form or details for inquiries.
Menu: View the food menu.
