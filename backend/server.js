const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const colors = require('colors');
const connectDB = require('./config/db');
const app = express();
app.use(cors({
  origin: 'http://localhost:5173', // allow Vite frontend
  credentials: true
}));
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.originalUrl}`);
  next();
});
// Load environment variables
dotenv.config();

console.log('Environment loaded, checking database connection variables...');
if (!process.env.MONGO_URI) {
  console.error('ERROR: MONGO_URI is missing in environment variables!');
  process.exit(1);
}

// Connect to MongoDB
connectDB();

const resumeRoutes = require('./routes/resumeRoutes');
const jobRoutes = require('./routes/jobRoutes');
const timelineRoutes = require('./routes/timelineRoutes');
const youtubeRoutes = require('./routes/youtubeRoutes');
const userRoutes = require('./routes/userRoutes');



app.use(express.json());
app.use(express.urlencoded({ extended: false }));

app.get('/', (req, res) => {
  res.send('Backend is running');
});

// Database test route
app.get('/api/test-db', async (req, res) => {
  try {
    console.log('Testing database connection...');
    const dbState = mongoose.connection.readyState;
    
    if (dbState === 1) {
      // Try a simple DB operation
      const count = await mongoose.connection.db.collection('users').countDocuments();
      console.log('Users collection count:', count);
      
      res.json({
        status: 'success',
        message: 'Database connection successful',
        dbState: 'connected',
        collections: {
          users: count
        }
      });
    } else {
      console.error('Database not connected, state:', dbState);
      res.status(500).json({
        status: 'error',
        message: 'Database not connected',
        dbState: dbState
      });
    }
  } catch (error) {
    console.error('Error testing database:', error);
    res.status(500).json({
      status: 'error',
      message: 'Database test failed',
      error: error.message
    });
  }
});

app.use('/api/users', userRoutes);
app.use('/api/resume', resumeRoutes);
app.use('/api/jobs', jobRoutes);
app.use('/api/timeline', timelineRoutes);
app.use('/api/youtube', youtubeRoutes);

// Add the skills routes
const skillsRoutes = require('./routes/skillsRoutes');
app.use('/api/skills', skillsRoutes);

// Add the AI analysis routes
const aiRoutes = require('./routes/aiRoutes');
app.use('/api/ai', aiRoutes);

app.use((req, res) => {
  console.warn(`No route matched for ${req.method} ${req.originalUrl}`);
  res.status(404).json({ error: 'Not Found' });
});

const PORT = process.env.PORT || 3011;
app.listen(PORT, () => console.log(`Backend running on port http://localhost:${PORT}`));
