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

// Static Pages
app.get('/', (req, res) => res.render('home'));
app.get('/about', (req, res) => res.render('about'));
app.get('/contact', (req, res) => res.render('contact'));
app.get('/login', (req, res) => res.render('login'));

// Login Auth
app.post('/login', (req, res) => {
    const { username, password } = req.body;
    if (username === 'admin' && password === 'password') {
        res.locals.user = { username };
        res.render('home', { user: username, auth: true });
    } else {
        res.render('login', { error: 'Invalid username or password' });
    }
});

// Bookings Guest View
app.get('/bookings/guest', (req, res) => res.render('bookings/bookingsGuest'));

// Admin Dashboard (Upcoming & Past)
app.get('/bookings/dashboard', (req, res) => {
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
app.get('/bookings/requests', async (req, res) => {
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
        console.log(`Forwarding approval for booking ID ${bookingId} to Flask API...`);
        
        const response = await axios.post(`http://localhost:5050/api/booking-requests/approve/${bookingId}`);
        
        // Optional: Check response content for better debugging
        if (response.data.success) {
            res.json({ success: true });
        } else {
            console.error('Flask API did not confirm success:', response.data);
            res.json({ success: false, message: 'Flask API responded without success flag.' });
        }
    } catch (error) {
        console.error('Error approving booking (frontend -> backend):', error.message);
        
        // Try to include backend error if possible
        const errData = error.response?.data || {};
        res.json({ success: false, error: errData.error || error.message });
    }
});


// Deny/Delete Booking
app.delete('/bookings/deny/:id', async (req, res) => {
    const bookingId = req.params.id;

    try {
        console.log(`Forwarding deletion for booking ID ${bookingId} to Flask API...`);
        
        const response = await axios.delete(`http://localhost:5050/api/booking-requests/delete/${bookingId}`);
        
        if (response.data.success) {
            res.json({ success: true, message: response.data.message });
        } else {
            console.error('Flask API did not confirm deletion:', response.data);
            res.json({ success: false, message: response.data.error || 'Unknown error during deletion.' });
        }
    } catch (error) {
        console.error('❌ Error deleting booking/client (frontend -> backend):', error.message);
        const errData = error.response?.data || {};
        res.json({ success: false, error: errData.error || error.message });
    }
});

/* ---------------------- SPECIALTIES ---------------------- */

app.get('/specialties/foreclosure', (req, res) => res.render('specialties/foreclosure'));
app.get('/specialties/probate', (req, res) => res.render('specialties/probate'));
app.get('/specialties/realEstate', (req, res) => res.render('specialties/realEstate'));

/* ---------------------- SERVER START ---------------------- */

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}/`);
});
