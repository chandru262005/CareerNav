const express = require('express');
const router = express.Router();
const { generateYouTubeRecommendations } = require('../controllers/youtubeController');

// Route to generate YouTube recommendations (supports both authenticated and non-authenticated requests)
router.post('/recommendations', generateYouTubeRecommendations);

// Alias route for backward compatibility
router.post('/', generateYouTubeRecommendations);

module.exports = router;
