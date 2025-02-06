import os

workers = 4
bind = f"0.0.0.0:{os.environ.get('PORT', '5001')}"
timeout = 120
accesslog = "-"
errorlog = "-" 