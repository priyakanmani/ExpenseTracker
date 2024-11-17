const express = require('express');
const router = express.Router();
const authenticate = require('../middleware/authMiddleware'); // Import the middleware

// Example of a route that requires authentication
router.get('/', authenticate, (req, res) => {
  // Here, you can access the user info via req.user (from the JWT)
  res.json({ message: 'This is a protected route', user: req.user });
});

module.exports = router;
