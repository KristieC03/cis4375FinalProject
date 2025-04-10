require('dotenv').config();
const session = require('express-session');
const express = require('express');
const axios = require('axios');
const methodOverride = require('method-override');
const bodyParser = require('body-parser');
const path = require('path');

const app = express();

/* ---------------------- Middleware ---------------------- */
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(methodOverride('_method'));

// Static files
app.use(express.static(path.join(__dirname, 'public')));

// Views
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Session
app.use(session({
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false
}));

// Set user info for all views
app.use((req, res, next) => {
    res.locals.user = req.session.user || null;
    next();
});

// Auth middleware
function isAdmin(req, res, next) {
    if (req.session.user && req.session.user.role === 'admin') {
        return next();
    } else {
        return res.status(403).send('Access denied: Admins only.');
    }
}
/* ---------------------- Routes ---------------------- */

// Static Pages
app.get('/', (req, res) => res.render('home'));
app.get('/about', (req, res) => res.render('about'));
app.get('/contact', (req, res) => res.render('contact'));
app.get('/login', (req, res) => res.render('login'));

// Login
app.post('/login', async (req, res) => {
    const { username, password } = req.body;

    try {
        // Call Flask API with Basic Auth
        const response = await axios.get('http://localhost:5050/authenticatedroute', {
            auth: {
                username,
                password
            },
            withCredentials: true
        });

        // If authorized
        if (response.status === 200) {
            req.session.user = {
                username,
                role: 'admin' // you can make this dynamic later if needed
            };
            return res.redirect('/');
        }

    } catch (error) {
        if (error.response) {
            console.error('Login failed:');
            console.error('Status:', error.response.status);
            console.error('Data:', error.response.data);
        } else {
            console.error('Login failed: No response received');
            console.error(error.message);
        }
    
        res.render('login', { error: 'Invalid username or password' });
    }    

    res.render('login', { error: 'Invalid username or password' });
});

// Logout
app.get('/logout', (req, res) => {
    req.session.destroy(() => {
        res.redirect('/');
    });
});

// Bookings Guest View
app.get('/bookings/guest', (req, res) => res.render('bookings/bookingsGuest'));

// Admin Dashboard
app.get('/bookings/dashboard', isAdmin, (req, res) => {
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

    res.render('bookings/bookingsDash', {
        upcomingAppointments,
        pastAppointments
    });
});

// Booking Requests
app.get('/bookings/requests', isAdmin, async (req, res) => {
    try {
        const response = await axios.get('http://localhost:5050/api/booking-requests');
        const data = response.data;

        const bookingRequests = data.map(booking => {
            const rawDate = new Date(booking.date);
            const hours = rawDate.getHours();
            const minutes = rawDate.getMinutes().toString().padStart(2, '0');
            const period = hours >= 12 ? 'PM' : 'AM';
            const formattedHour = hours % 12 === 0 ? 12 : hours % 12;

            return {
                id: booking.Booking_ID,
                firstName: booking.firstName,
                lastName: booking.lastName,
                date: rawDate.toISOString().split('T')[0],
                time: `${formattedHour}:${minutes}`,
                period,
                email: booking.email,
                phone: booking.phone,
                serviceType: booking.serviceType,
                notes: booking.notes
            };
        });

        res.render('bookings/bookingsRequest', { bookingRequests });
    } catch (error) {
        console.error('Error fetching booking requests:', error.message);
        res.render('bookings/bookingsRequest', { bookingRequests: [] });
    }
});

// Approve Booking
app.post('/bookings/approve/:id', async (req, res) => {
    const bookingId = req.params.id;

    try {
        const response = await axios.post(`http://localhost:5050/api/booking-requests/approve/${bookingId}`);
        if (response.data.success) {
            res.json({ success: true });
        } else {
            res.json({ success: false, message: 'Flask API responded without success flag.' });
        }
    } catch (error) {
        const errData = error.response?.data || {};
        res.json({ success: false, error: errData.error || error.message });
    }
});

// Deny/Delete Booking
app.delete('/bookings/deny/:id', async (req, res) => {
    const bookingId = req.params.id;

    try {
        const response = await axios.delete(`http://localhost:5050/api/booking-requests/delete/${bookingId}`);
        if (response.data.success) {
            res.json({ success: true, message: response.data.message });
        } else {
            res.json({ success: false, message: response.data.error || 'Unknown error during deletion.' });
        }
    } catch (error) {
        const errData = error.response?.data || {};
        res.json({ success: false, error: errData.error || error.message });
    }
});

// Specialties
app.get('/specialties/foreclosure', (req, res) => res.render('specialties/foreclosure'));
app.get('/specialties/probate', (req, res) => res.render('specialties/probate'));
app.get('/specialties/realEstate', (req, res) => res.render('specialties/realEstate'));

/* ---------------------- Start Server ---------------------- */
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}/`);
});
