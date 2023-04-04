const express = require("express");
const bodyParser = require("body-parser");
const morgan = require("morgan");

const { readFileSync } = require("fs");

const app = express();
const port = 3000;
let counter = 0;

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

app.use(morgan("dev"));

const data = readFileSync("./db.json");
const db = JSON.parse(data);

resetCounters();

app.get("/api/wxckedeye/v1/dashboard", (req, res) => {
    incrementCounters();

    res.send(db.dashboard);
});

app.listen(port, () =>
    console.log(`wXcked Eye API Poller Program Listening on Port ${port}!`)
);

function resetCounters() {
    for (const metric of ["PktCounters", "ByteCounters"]) {
        for (const key in db.dashboard.xnicTotals[metric]) {
            db.dashboard.xnicTotals[metric][key] = 0;
        }
    }

    for (const agent in db.dashboard.xnics) {
        for (const metric of ["PktCounters", "ByteCounters"]) {
            for (const key in db.dashboard.xnicTotals[metric]) {
                db.dashboard.xnics[agent][metric][key] = 0;
            }
        }
    }
}

function incrementCounters() {
    if (counter > 1000) {
        resetCounters();
        counter = 0;
    }

    for (const metric of ["PktCounters", "ByteCounters"]) {
        for (const key in db.dashboard.xnicTotals[metric]) {
            db.dashboard.xnicTotals[metric][key] +=
                Math.floor(Math.random() * 100000) + 5000;
        }
    }

    for (const agent in db.dashboard.xnics) {
        for (const metric of ["PktCounters", "ByteCounters"]) {
            for (const key in db.dashboard.xnicTotals[metric]) {
                db.dashboard.xnics[agent][metric][key] +=
                    Math.floor(Math.random() * 100000) + 10000;
            }
        }
    }

    counter++;
}
