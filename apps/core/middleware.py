# Middleware for Maintenance Mode
# apps/core/middleware.py

import os
from django.http import HttpResponse
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.deprecation import MiddlewareMixin


class MaintenanceModeMiddleware(MiddlewareMixin):
    """
    Middleware to enable maintenance mode during updates
    """
    
    def process_request(self, request):
        # Check if maintenance mode is enabled
        maintenance_file = os.path.join(settings.BASE_DIR, '.maintenance')
        
        if os.path.exists(maintenance_file):
            # Skip maintenance mode for superusers
            if request.user.is_authenticated and request.user.is_superuser:
                return None
                
            # Skip maintenance mode for specific paths (health checks, API endpoints)
            exempt_paths = [
                '/health/',
                '/admin/',
                '/api/system/status/',
                '/static/',
                '/media/',
            ]
            
            if any(request.path.startswith(path) for path in exempt_paths):
                return None
            
            # Return maintenance page
            try:
                # Try to render a custom maintenance template
                maintenance_content = render_to_string('maintenance.html', {
                    'message': 'ZAIN HMS is currently under maintenance. We\'ll be back shortly!'
                })
            except:
                # Fallback to simple HTML
                maintenance_content = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>System Under Maintenance - ZAIN HMS</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body {
                            font-family: 'Segoe UI', Arial, sans-serif;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            margin: 0;
                            padding: 0;
                            min-height: 100vh;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                        }
                        .maintenance-container {
                            text-align: center;
                            background: rgba(255,255,255,0.1);
                            padding: 60px 40px;
                            border-radius: 20px;
                            backdrop-filter: blur(10px);
                            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                            max-width: 600px;
                            margin: 20px;
                        }
                        .maintenance-icon {
                            font-size: 80px;
                            margin-bottom: 30px;
                            animation: pulse 2s infinite;
                        }
                        @keyframes pulse {
                            0% { transform: scale(1); }
                            50% { transform: scale(1.05); }
                            100% { transform: scale(1); }
                        }
                        h1 {
                            font-size: 2.5em;
                            margin-bottom: 20px;
                            font-weight: 300;
                        }
                        p {
                            font-size: 1.2em;
                            margin-bottom: 30px;
                            line-height: 1.6;
                        }
                        .progress-bar {
                            background: rgba(255,255,255,0.2);
                            height: 4px;
                            border-radius: 2px;
                            overflow: hidden;
                            margin-top: 30px;
                        }
                        .progress-fill {
                            background: #4CAF50;
                            height: 100%;
                            border-radius: 2px;
                            animation: loading 3s ease-in-out infinite;
                        }
                        @keyframes loading {
                            0% { width: 0%; }
                            50% { width: 70%; }
                            100% { width: 100%; }
                        }
                        .footer {
                            margin-top: 40px;
                            font-size: 0.9em;
                            opacity: 0.8;
                        }
                    </style>
                </head>
                <body>
                    <div class="maintenance-container">
                        <div class="maintenance-icon">🔧</div>
                        <h1>System Under Maintenance</h1>
                        <p>ZAIN HMS is currently being updated with new features and improvements. We'll be back online shortly.</p>
                        <p>Thank you for your patience!</p>
                        <div class="progress-bar">
                            <div class="progress-fill"></div>
                        </div>
                        <div class="footer">
                            <p>If this is urgent, please contact technical support.</p>
                        </div>
                    </div>
                    <script>
                        // Auto-refresh every 30 seconds
                        setTimeout(function() {
                            window.location.reload();
                        }, 30000);
                    </script>
                </body>
                </html>
                """
            
            return HttpResponse(maintenance_content, status=503)
        
        return None