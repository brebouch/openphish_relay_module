import os

#from __version__ import VERSION


class Config:
    #VERSION = VERSION

    SECRET_KEY = os.environ.get('SECRET_KEY')

    API_URL = "http://localhost:4000" # the umbrella backend simulator
    API_PATH = "/domains/categorization/{observable}"
    API_SOURCE = "/domains/categorization/{observable}"

    
    # Supported types with rules
    CCT_OBSERVABLE_TYPES = {
        'url': {'sep': '://'},
        'ip': {},
        'domain': {}
    }
   
    CTR_HEADERS = {
		# user agent to use when calling the 3rd Party Solution
        'User-Agent': ('SecureX Threat Response Integrations '
                       '<tr-integrations-support@cisco.com>')
    }   
    
    # Supported types of verdict
    DISPOSITIONS = {
        'clean': (1, 'Clean'),
        'malicious': (2, 'Malicious'),
        'suspicious': (3, 'Suspicious'),
        'common': (4, 'Common'),
        'unknown': (5, 'Unknown')
    }    