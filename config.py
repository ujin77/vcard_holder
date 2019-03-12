class Config:
    API_KEY = '1234567890'
    VCARD_SERVER = 'http://localhost:8082'


class DevelopmentConfig(Config):
    DEBUG = True


class TestConfig(Config):
    DEBUG = True
    TESTING = True


class ProductionConfig(Config):
    DEBUG = False
