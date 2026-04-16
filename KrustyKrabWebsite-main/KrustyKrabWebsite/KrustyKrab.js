document.addEventListener("DOMContentLoaded", function () {
    const reservationsDiv = document.getElementById("reservations");

    // Fetch and display reservations
    fetch("http://localhost:3000/reservations")
        .then(response => response.text())
        .then(data => {
            const reservations = parseCSV(data);
            displayReservations(reservations);
        })
        .catch(error => {
            console.error("Error fetching reservations:", error);
            reservationsDiv.innerHTML = `<p>Error loading reservations: ${error.message}</p>`;
        });

    // Parse CSV data into an array of objects
    function parseCSV(csv) {
        const rows = csv.split("\n").map(row => row.split(","));
        const headers = rows[0]; // Get column headers
        const data = rows.slice(1); // Skip header row

        const allowedHeaders = ["Date", "Time", "Party Size"];
        return data.map(row => {
            const reservation = {};
            row.forEach((value, index) => {
                const header = headers[index]?.trim();
                if (allowedHeaders.includes(header)) {
                    reservation[header] = value.trim();
                }
            });
            return reservation;
        });
    }

    // Display reservations in a table
    function displayReservations(reservations) {
        if (!reservations || reservations.length === 0) {
            reservationsDiv.innerHTML = "<p>No reservations found.</p>";
            return;
        }

        const table = document.createElement("table");
        table.border = "1";

        // Add table headers
        const headerRow = document.createElement("tr");
        Object.keys(reservations[0]).forEach(header => {
            const th = document.createElement("th");
            th.textContent = header;
            headerRow.appendChild(th);
        });
        table.appendChild(headerRow);

        // Add table rows
        reservations.forEach(reservation => {
            const row = document.createElement("tr");
            Object.values(reservation).forEach(value => {
                const td = document.createElement("td");
                td.textContent = value || "N/A";
                row.appendChild(td);
            });
            table.appendChild(row);
        });

        reservationsDiv.innerHTML = ""; // Clear previous content
        reservationsDiv.appendChild(table);
    }

    // Helper functions for normalization
    function normalizeDate(dateString) {
        const [month, day, year] = dateString.split("/");
        return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
    }

    function normalizeTime(timeString) {
        const [time, modifier] = timeString.split(" ");
        let [hours, minutes] = time.split(":").map(Number);
        if (modifier === "PM" && hours < 12) hours += 12;
        if (modifier === "AM" && hours === 12) hours = 0;
        return `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}`;
    }

    // Filter reservations by date
    function filterReservations(reservations, searchDate) {
        return reservations.filter(reservation => {
            const reservationDate = normalizeDate(reservation.Date);
            return reservationDate === searchDate;
        });
    }

    // Add event listener for the search functionality
    document.getElementById("searchButton").addEventListener("click", function () {
        const searchDate = document.getElementById("searchDate").value; // YYYY-MM-DD from input
        if (!searchDate) {
            alert("Please select a date.");
            return;
        }

        fetch("http://localhost:3000/reservations")
            .then(response => response.text())
            .then(data => {
                const reservations = parseCSV(data);
                const filteredReservations = filterReservations(reservations, searchDate);
                displayReservations(filteredReservations);
            })
            .catch(error => {
                console.error("Error filtering reservations:", error);
                reservationsDiv.innerHTML = `<p>Error loading reservations: ${error.message}</p>`;
            });
    });

    // Check if a date and time are available
    function isTimeSlotAvailable(reservations, date, time) {
        const normalizedTime = normalizeTime(time);
        return !reservations.some(reservation => {
            const reservationDate = normalizeDate(reservation.Date);
            const reservationTime = normalizeTime(reservation.Time);
            return reservationDate === date && reservationTime === normalizedTime;
        });
    }

    // Validate reservation before submission
    document.getElementById("reservationForm").addEventListener("submit", function (event) {
        event.preventDefault();

        const date = document.getElementById("date").value; // YYYY-MM-DD from input
        const time = document.getElementById("time").value; // HH:MM from input
        if (!date || !time) {
            alert("Please select both a date and a time.");
            return;
        }

        fetch("http://localhost:3000/reservations")
            .then(response => response.text())
            .then(data => {
                const reservations = parseCSV(data);
                if (isTimeSlotAvailable(reservations, date, time)) {
                    alert("Reservation is available! Proceeding...");
                    // Add form submission logic here
                } else {
                    alert("This time slot is already booked. Please choose another.");
                }
            })
            .catch(error => {
                console.error("Error validating reservation:", error);
                alert("Could not validate the reservation. Try again later.");
            });
    });
});
