const Admin = require('../models/Admin');
const { hashPassword, matchPassword, generateToken } = require('../utils/auth/authUtils');
const crypto = require('crypto');
const { sendVerificationEmail } = require('../utils/emailService');
const { validatePasswordStrength } = require('../utils/passwordValidator');

/**
 * @desc   Register a new admin
 * @route  POST /api/admin/signup
 * @access Public (initial setup) or Protected (super_admin only for adding new admins)
 */
exports.registerAdmin = async (req, res) => {
  try {
    const { name, email, password, confirmPassword } = req.body;

    // Validation
    if (!name || !email || !password || !confirmPassword) {
      return res.status(400).json({
        success: false,
        error: 'Please provide all required fields',
      });
    }

    if (password !== confirmPassword) {
      return res.status(400).json({
        success: false,
        error: 'Passwords do not match',
      });
    }

    // Check if admin already exists
    const existingAdmin = await Admin.findOne({ email });
    if (existingAdmin) {
      return res.status(409).json({
        success: false,
        error: 'Admin with this email already exists',
      });
    }

    // Validate password strength
    const validation = validatePasswordStrength(password);
    if (!validation.isValid) {
      return res.status(400).json({
        success: false,
        error: 'Password does not meet requirements',
        details: validation.errors,
      });
    }

    // Hash password
    const hashedPassword = await hashPassword(password);

    // Generate verification token
    const verificationToken = crypto.randomBytes(32).toString('hex');
    const verificationTokenHash = crypto
      .createHash('sha256')
      .update(verificationToken)
      .digest('hex');

    // Create admin
    const admin = await Admin.create({
      name,
      email,
      password: hashedPassword,
      verificationToken: verificationTokenHash,
      verificationTokenExpiry: Date.now() + 24 * 60 * 60 * 1000, // 24 hours
      isVerified: false,
    });

    // Send verification email
    try {
      const frontendUrl = process.env.FRONTEND_URL_ADMIN || process.env.FRONTEND_URL || 'http://localhost:5173';
      const verificationUrl = `${frontendUrl}/verify-email?token=${verificationToken}&email=${encodeURIComponent(admin.email)}`;
      await sendVerificationEmail(admin.email, verificationToken, verificationUrl);
    } catch (emailError) {
      console.error('Failed to send verification email:', emailError);
      // Don't fail the registration, just notify
    }

    res.status(201).json({
      success: true,
      message: 'Admin registered successfully. Please verify your email.',
      data: {
        _id: admin._id,
        name: admin.name,
        email: admin.email,
        isVerified: admin.isVerified,
      },
    });
  } catch (error) {
    console.error('Admin registration error:', error);
    res.status(500).json({
      success: false,
      error: 'Error registering admin',
      details: error.message,
    });
  }
};

/**
 * @desc   Login admin
 * @route  POST /api/admin/login
 * @access Public
 */
exports.loginAdmin = async (req, res) => {
  try {
    const { email, password } = req.body;

    // Validation
    if (!email || !password) {
      return res.status(400).json({
        success: false,
        error: 'Please provide email and password',
      });
    }

    // Find admin and include password
    const admin = await Admin.findOne({ email }).select('+password');

    if (!admin) {
      return res.status(401).json({
        success: false,
        error: 'Invalid credentials',
      });
    }

    // Check if admin is verified
    if (!admin.isVerified) {
      return res.status(403).json({
        success: false,
        error: 'Please verify your email before logging in',
      });
    }

    // Check if admin is active
    if (admin.status === 'suspended') {
      return res.status(403).json({
        success: false,
        error: 'Your account has been suspended',
      });
    }

    // Check if admin is inactive
    if (admin.status === 'inactive') {
      return res.status(403).json({
        success: false,
        error: 'Your account is inactive',
      });
    }

    // Check password
    const isPasswordCorrect = await matchPassword(password, admin.password);

    if (!isPasswordCorrect) {
      return res.status(401).json({
        success: false,
        error: 'Invalid credentials',
      });
    }

    // Update last login
    admin.lastLogin = new Date();
    await admin.save();

    // Generate token
    const token = generateToken(admin._id, 'admin');

    res.status(200).json({
      success: true,
      message: 'Login successful',
      token,
      data: {
        _id: admin._id,
        name: admin.name,
        email: admin.email,
        role: admin.role,
        permissions: admin.permissions,
        isVerified: admin.isVerified,
      },
    });
  } catch (error) {
    console.error('Admin login error:', error);
    res.status(500).json({
      success: false,
      error: 'Error logging in',
      details: error.message,
    });
  }
};

/**
 * @desc   Verify admin email
 * @route  GET /api/admin/verify?token=verificationToken
 * @access Public
 */
exports.verifyAdminEmail = async (req, res) => {
  try {
    const { token } = req.query;

    if (!token) {
      return res.status(400).json({
        success: false,
        error: 'Verification token is required',
      });
    }

    // Hash the token to compare with stored hash
    const tokenHash = crypto.createHash('sha256').update(token).digest('hex');

    // Find admin with matching verification token
    const admin = await Admin.findOne({
      verificationToken: tokenHash,
      verificationTokenExpiry: { $gt: Date.now() },
    });

    if (!admin) {
      return res.status(400).json({
        success: false,
        error: 'Invalid or expired verification token',
      });
    }

    // Update admin
    admin.isVerified = true;
    admin.verificationToken = undefined;
    admin.verificationTokenExpiry = undefined;
    await admin.save();

    res.status(200).json({
      success: true,
      message: 'Email verified successfully',
      data: {
        _id: admin._id,
        name: admin.name,
        email: admin.email,
        isVerified: admin.isVerified,
      },
    });
  } catch (error) {
    console.error('Email verification error:', error);
    res.status(500).json({
      success: false,
      error: 'Error verifying email',
      details: error.message,
    });
  }
};

/**
 * @desc   Resend verification email
 * @route  POST /api/admin/resend-verification
 * @access Public
 */
exports.resendVerificationEmail = async (req, res) => {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({
        success: false,
        error: 'Email is required',
      });
    }

    const admin = await Admin.findOne({ email });

    if (!admin) {
      return res.status(404).json({
        success: false,
        error: 'Admin not found',
      });
    }

    if (admin.isVerified) {
      return res.status(400).json({
        success: false,
        error: 'Email is already verified',
      });
    }

    // Generate new verification token
    const verificationToken = crypto.randomBytes(32).toString('hex');
    const verificationTokenHash = crypto
      .createHash('sha256')
      .update(verificationToken)
      .digest('hex');

    admin.verificationToken = verificationTokenHash;
    admin.verificationTokenExpiry = Date.now() + 24 * 60 * 60 * 1000;
    await admin.save();

    // Send verification email
    try {
      const frontendUrl = process.env.FRONTEND_URL_ADMIN || process.env.FRONTEND_URL || 'http://localhost:5173';
      const verificationUrl = `${frontendUrl}/verify-email?token=${verificationToken}&email=${encodeURIComponent(admin.email)}`;
      await sendVerificationEmail(admin.email, verificationToken, verificationUrl);
    } catch (emailError) {
      console.error('Failed to send verification email:', emailError);
    }

    res.status(200).json({
      success: true,
      message: 'Verification email sent successfully',
    });
  } catch (error) {
    console.error('Resend verification error:', error);
    res.status(500).json({
      success: false,
      error: 'Error resending verification email',
      details: error.message,
    });
  }
};

/**
 * @desc   Get admin profile
 * @route  GET /api/admin/profile
 * @access Protected (admin)
 */
exports.getAdminProfile = async (req, res) => {
  try {
    const admin = await Admin.findById(req.admin._id);

    if (!admin) {
      return res.status(404).json({
        success: false,
        error: 'Admin not found',
      });
    }

    res.status(200).json({
      success: true,
      data: admin,
    });
  } catch (error) {
    console.error('Get admin profile error:', error);
    res.status(500).json({
      success: false,
      error: 'Error fetching admin profile',
      details: error.message,
    });
  }
};

/**
 * @desc   Update admin profile
 * @route  PUT /api/admin/profile
 * @access Protected (admin)
 */
exports.updateAdminProfile = async (req, res) => {
  try {
    const { name, notes } = req.body;

    const admin = await Admin.findById(req.admin._id);

    if (!admin) {
      return res.status(404).json({
        success: false,
        error: 'Admin not found',
      });
    }

    if (name) admin.name = name;
    if (notes !== undefined) admin.notes = notes;

    await admin.save();

    res.status(200).json({
      success: true,
      message: 'Profile updated successfully',
      data: admin,
    });
  } catch (error) {
    console.error('Update admin profile error:', error);
    res.status(500).json({
      success: false,
      error: 'Error updating admin profile',
      details: error.message,
    });
  }
};

/**
 * @desc   Change admin password
 * @route  PUT /api/admin/change-password
 * @access Protected (admin)
 */
exports.changeAdminPassword = async (req, res) => {
  try {
    const { currentPassword, newPassword, confirmPassword } = req.body;

    if (!currentPassword || !newPassword || !confirmPassword) {
      return res.status(400).json({
        success: false,
        error: 'Please provide all required fields',
      });
    }

    if (newPassword !== confirmPassword) {
      return res.status(400).json({
        success: false,
        error: 'New passwords do not match',
      });
    }

    const admin = await Admin.findById(req.admin._id).select('+password');

    if (!admin) {
      return res.status(404).json({
        success: false,
        error: 'Admin not found',
      });
    }

    // Verify current password
    const isPasswordCorrect = await matchPassword(currentPassword, admin.password);

    if (!isPasswordCorrect) {
      return res.status(401).json({
        success: false,
        error: 'Current password is incorrect',
      });
    }

    // Validate new password strength
    const validation = validatePasswordStrength(newPassword);
    if (!validation.isValid) {
      return res.status(400).json({
        success: false,
        error: 'New password does not meet requirements',
        details: validation.errors,
      });
    }

    // Hash new password
    admin.password = await hashPassword(newPassword);
    await admin.save();

    res.status(200).json({
      success: true,
      message: 'Password changed successfully',
    });
  } catch (error) {
    console.error('Change password error:', error);
    res.status(500).json({
      success: false,
      error: 'Error changing password',
      details: error.message,
    });
  }
};

/**
 * @desc   Forgot password - send reset email
 * @route  POST /api/admin/forgot-password
 * @access Public
 */
exports.forgotAdminPassword = async (req, res) => {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({
        success: false,
        error: 'Email is required',
      });
    }

    const admin = await Admin.findOne({ email });

    if (!admin) {
      return res.status(404).json({
        success: false,
        error: 'Admin not found',
      });
    }

    // Generate password reset token
    const resetToken = crypto.randomBytes(32).toString('hex');
    const resetTokenHash = crypto
      .createHash('sha256')
      .update(resetToken)
      .digest('hex');

    admin.passwordResetToken = resetTokenHash;
    admin.passwordResetExpiry = Date.now() + 1 * 60 * 60 * 1000; // 1 hour
    await admin.save();

    // Send reset email
    try {
      const resetUrl = `${process.env.FRONTEND_URL || 'http://localhost:5173'}/reset-password?token=${resetToken}`;
      const { sendPasswordResetEmail } = require('../utils/emailService');
      await sendPasswordResetEmail(email, resetToken, resetUrl);
      console.log(`Password reset email sent to ${email}`);
    } catch (emailError) {
      console.error('Failed to send reset email:', emailError);
      // Continue anyway - token is still valid for manual reset
    }

    res.status(200).json({
      success: true,
      message: 'Password reset email sent successfully',
    });
  } catch (error) {
    console.error('Forgot password error:', error);
    res.status(500).json({
      success: false,
      error: 'Error processing password reset request',
      details: error.message,
    });
  }
};

/**
 * @desc   Reset admin password
 * @route  POST /api/admin/reset-password
 * @access Public
 */
exports.resetAdminPassword = async (req, res) => {
  try {
    const { token, password } = req.body;

    if (!token || !password) {
      return res.status(400).json({
        success: false,
        error: 'Token and new password are required',
      });
    }

    if (password.length < 8) {
      return res.status(400).json({
        success: false,
        error: 'Password must be at least 8 characters long',
      });
    }

    // Hash the token
    const tokenHash = crypto.createHash('sha256').update(token).digest('hex');

    // Find admin with matching reset token
    const admin = await Admin.findOne({
      passwordResetToken: tokenHash,
      passwordResetExpiry: { $gt: Date.now() },
    });

    if (!admin) {
      return res.status(400).json({
        success: false,
        error: 'Invalid or expired reset token',
      });
    }

    // Update password
    const hashedPassword = await hashPassword(password);
    admin.password = hashedPassword;
    admin.passwordResetToken = undefined;
    admin.passwordResetExpiry = undefined;
    await admin.save();

    res.status(200).json({
      success: true,
      message: 'Password reset successfully',
    });
  } catch (error) {
    console.error('Reset password error:', error);
    res.status(500).json({
      success: false,
      error: 'Error resetting password',
      details: error.message,
    });
  }
};
