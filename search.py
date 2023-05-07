from Functions.Search.search import Search
from Functions.Auth.auth import Authenticate
from global_var import ROOT

if __name__ == '__main__':
    service = Authenticate.gmailAuthenticate()
    Search(service, ROOT).processMails()
