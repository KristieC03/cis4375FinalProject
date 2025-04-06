const express = require('express');
const axios = require('axios');
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

app.get('/bookings/dashboard', (req, res) => {
    console.log('Rendering bookings dashboard...');

    const upcomingAppointments = [
        {
            firstName: 'John',
            lastName: 'Doe',
            email: 'john.doe@example.com',
            phone: '123-456-7890',
            date: '2025-04-06',
            time: '10:00',
            period: 'AM',
            serviceType: 'Consultation',
            notes: 'First-time visit'
        },
        {
            firstName: 'Jane',
            lastName: 'Smith',
            email: 'jane.smith@example.com',
            phone: '321-654-0987',
            date: '2025-04-08',
            time: '2:30',
            period: 'PM',
            serviceType: 'Probate Law',
            notes: ''
        }
    ];

    const pastAppointments = [
        {
            firstName: 'Alice',
            lastName: 'Brown',
            email: 'alice.brown@example.com',
            phone: '456-789-0123',
            date: '2025-03-30',
            time: '1:00',
            period: 'PM',
            serviceType: 'Real Estate',
            notes: 'Had previous case'
        },
        {
            firstName: 'Tom',
            lastName: 'Johnson',
            email: 'tom.johnson@example.com',
            phone: '987-654-3210',
            date: '2025-04-01',
            time: '11:00',
            period: 'AM',
            serviceType: 'Foreclosure Defense',
            notes: ''
        }
    ];

    console.log('Sending to EJS:', { upcomingAppointments, pastAppointments });

    res.render('bookings/bookingsDash', {
        upcomingAppointments,
        pastAppointments
    });
});

app.get('/bookings/requests', (req, res) => {
    const bookingRequests = [
      {
        firstName: 'Jane',
        lastName: 'Doe',
        date: '2025-04-15',
        time: '3:00',
        period: 'PM',
        email: 'jane@example.com',
        phone: '555-123-4567',
        serviceType: 'Consultation',
        notes: 'Needs to reschedule.'
      },
      {
        firstName: 'John',
        lastName: 'Smith',
        date: '2025-04-18',
        time: '10:00',
        period: 'AM',
        email: 'john.smith@example.com',
        phone: '555-987-6543',
        serviceType: 'Legal Advice',
        notes: ''
      }
    ];
  
    // this MUST match the filename in your views folder
    res.render('bookings/bookingsRequest', { bookingRequests });
  });
  
  
  

// Specialties
app.get('/specialties/foreclosure', (req, res) => res.render('specialties/foreclosure'));
app.get('/specialties/probate', (req, res) => res.render('specialties/probate'));
app.get('/specialties/realEstate', (req, res) => res.render('specialties/realEstate'));

/* ---------------------- SERVER START ---------------------- */

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}/`);
});
