const express = require('express');
const methodOverride = require('method-override');
const bodyParser = require('body-parser');
const path = require('path');
const app = express();

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(methodOverride('_method'));

// Views
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Static files (optional, if using CSS or images)
app.use(express.static(path.join(__dirname, 'public')));

// Simulate login session
app.use((req, res, next) => {
    res.locals.user = null;
    next();
});


/* ---------------------- FRONTEND ROUTES ---------------------- */

app.get('/', (req, res) => res.render('home'));
app.get('/about', (req, res) => res.render('about'));
app.get('/contact', (req, res) => res.render('contact'));
app.get('/login', (req, res) => res.render('login'));

app.post('/login', (req, res) => {
    const { username, password } = req.body;
    if (username === 'admin' && password === 'password') {
        res.locals.user = { username };
        res.render('home', { user: username, auth: true });
    } else {
        res.render('login', { error: 'Invalid username or password' });
    }
});

// Bookings
app.get('/bookings/guest', (req, res) => res.render('bookings/bookingsGuest'));
app.get('/bookings/dashboard', (req, res) => res.render('bookings/bookingsDash'));
app.get('/bookings/requests', (req, res) => res.render('bookings/bookingsRequest'));

// Specialties
app.get('/specialties/foreclosure', (req, res) => res.render('specialties/foreclosure'));
app.get('/specialties/general', (req, res) => res.render('specialties/general'));
app.get('/specialties/probate', (req, res) => res.render('specialties/probate'));
app.get('/specialties/realEstate', (req, res) => res.render('specialties/realEstate'));

/* ---------------------- SERVER START ---------------------- */

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}/`);
});
