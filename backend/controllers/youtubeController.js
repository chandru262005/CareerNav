// Controller to generate YouTube recommendations using Python script
const { spawn } = require('child_process');

exports.generateYouTubeRecommendations = async (req, res) => {
  try {
    const { current_skills, target_job, timeframe_months, additional_context } = req.body;
    
    console.log('youtubeController: generateYouTubeRecommendations called with:', {
      current_skills,
      target_job,
      timeframe_months,
      additional_context
    });
    
    if (!current_skills || !target_job || !timeframe_months) {
      console.error('youtubeController: Missing required fields');
      return res.status(400).json({ 
        error: 'current_skills, target_job, and timeframe_months are required' 
      });
    }

    // Prepare arguments for Python script (mode = "youtube")
    const args = [
      JSON.stringify(current_skills),
      target_job,
      timeframe_months.toString(),
      additional_context ? JSON.stringify(additional_context) : '{}',
      'youtube'  // mode: "youtube" for YouTube-based timeline
    ];

    console.log('youtubeController: Spawning Python process with args:', args);
    const py = spawn('python', ['utils/gemini_timeline.py', ...args]);
    let data = '';
    let error = '';

    py.stdout.on('data', (chunk) => {
      data += chunk.toString();
      console.log('youtubeController: Python stdout:', chunk.toString());
    });

    py.stderr.on('data', (chunk) => {
      // Log stderr output but don't treat it as a fatal error
      console.log(`gemini_timeline.py log: ${chunk.toString().trim()}`);
      
      // Only add to error if it's an actual error, not just a warning
      if (chunk.toString().toLowerCase().includes('error:') || chunk.toString().toLowerCase().includes('exception:')) {
        error += chunk.toString();
      }
    });

    py.on('close', (code) => {
      console.log('youtubeController: Python process closed with code:', code, 'error:', error, 'data length:', data.length);
      
      if ((code !== 0 || error) && !data) {
        console.error('youtubeController: Error detected - code:', code, 'error:', error);
        return res.status(500).json({ error: error || 'Failed to generate YouTube recommendations' });
      }

      try {
        const result = JSON.parse(data);
        console.log('youtubeController: Successfully parsed result');
        res.json(result);
      } catch (e) {
        console.error('youtubeController: Failed to parse JSON:', e, 'data:', data);
        res.status(500).json({ error: 'Invalid response from YouTube recommendations generator' });
      }
    });
  } catch (err) {
    console.error('youtubeController: Exception:', err);
    res.status(500).json({ error: 'Something went wrong' });
  }
};
