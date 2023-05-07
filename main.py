from Functions.Auth.auth import Authenticate
from Functions.Parse.Parser import EmailParser

if __name__ == '__main__':
    # get the Gmail API service
    service = Authenticate.gmailAuthenticate()
    # fetch all mails
    EmailParser(service).fetchStoreMessages(query="is:")
