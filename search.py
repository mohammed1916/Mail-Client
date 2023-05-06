from Functions.Search.main import Search
from Functions.Auth.auth import Authenticate

service = Authenticate.gmailAuthenticate()
Search(service).processMails()
