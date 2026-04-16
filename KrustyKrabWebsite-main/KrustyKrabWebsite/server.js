const express = require("express");
const axios = require("axios");
const cors = require("cors");

const app = express();
const PORT = 3000;

const sheetURL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQApFLsPd53rVrZMOpyTwLEYBU7mjEUe68CCNke40gU4VV_z3GlPW3gNgtzYC5duw-a-lV6hXs-_NOS/pub?output=csv";

app.use(cors());

app.get("/reservations", async (req, res) => {
    try {
        const response = await axios.get(sheetURL);
        res.send(response.data);
    } catch (error) {
        console.error("Error fetching reservations:", error.message);
        res.status(500).send("Failed to fetch reservations");
    }
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});

