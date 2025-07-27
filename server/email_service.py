import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from security_logger import log_security_event

class EmailService:
    """Basic SMTP email service for password resets."""
    
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'localhost')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.smtp_use_tls = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
        self.from_email = os.environ.get('FROM_EMAIL', 'noreply@workout-tracker.local')
        self.app_url = os.environ.get('APP_URL', 'http://localhost:8080')
    
    def send_password_reset_email(self, to_email, username, reset_token):
        """Send password reset email."""
        try:
            reset_url = f"{self.app_url}/reset-password?token={reset_token}"
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Password Reset - Workout Tracker'
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Create HTML content
            html_content = f"""
            <html>
              <body>
                <h2>Password Reset Request</h2>
                <p>Hello {username},</p>
                <p>You have requested a password reset for your Workout Tracker account.</p>
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This link will expire in 1 hour.</p>
                <p>If you did not request this reset, please ignore this email.</p>
                <br>
                <p>Best regards,<br>Workout Tracker Team</p>
              </body>
            </html>
            """
            
            # Create text content
            text_content = f"""
            Password Reset Request
            
            Hello {username},
            
            You have requested a password reset for your Workout Tracker account.
            
            Copy and paste this link to reset your password:
            {reset_url}
            
            This link will expire in 1 hour.
            
            If you did not request this reset, please ignore this email.
            
            Best regards,
            Workout Tracker Team
            """
            
            # Attach parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            log_security_event('PASSWORD_RESET_EMAIL_SENT', f'Password reset email sent to {to_email}')
            return True, "Password reset email sent successfully"
            
        except Exception as e:
            log_security_event('PASSWORD_RESET_EMAIL_ERROR', f'Failed to send password reset email to {to_email}: {str(e)}')
            return False, "Failed to send password reset email"
    
    def send_admin_created_user_email(self, to_email, username, temp_password):
        """Send email when admin creates a new user."""
        try:
            login_url = f"{self.app_url}"
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Your Workout Tracker Account - Action Required'
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Create HTML content
            html_content = f"""
            <html>
              <body>
                <h2>Welcome to Workout Tracker</h2>
                <p>Hello {username},</p>
                <p>An administrator has created an account for you.</p>
                <p><strong>Your login credentials:</strong></p>
                <ul>
                  <li>Username: {username}</li>
                  <li>Temporary Password: {temp_password}</li>
                </ul>
                <p><a href="{login_url}">Login to Workout Tracker</a></p>
                <p><strong>IMPORTANT:</strong> You will be required to change your password on first login.</p>
                <br>
                <p>Best regards,<br>Workout Tracker Team</p>
              </body>
            </html>
            """
            
            # Create text content
            text_content = f"""
            Welcome to Workout Tracker
            
            Hello {username},
            
            An administrator has created an account for you.
            
            Your login credentials:
            Username: {username}
            Temporary Password: {temp_password}
            
            Login at: {login_url}
            
            IMPORTANT: You will be required to change your password on first login.
            
            Best regards,
            Workout Tracker Team
            """
            
            # Attach parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            log_security_event('USER_CREATION_EMAIL_SENT', f'New user email sent to {to_email}')
            return True, "User creation email sent successfully"
            
        except Exception as e:
            log_security_event('USER_CREATION_EMAIL_ERROR', f'Failed to send user creation email to {to_email}: {str(e)}')
            return False, "Failed to send user creation email"

# Global email service instance
email_service = EmailService()
