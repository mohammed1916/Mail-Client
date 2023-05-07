from global_var import ROOT
import os
import pickle
import sys
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']


class Authenticate:
    def gmailAuthenticate():
        creds = None
        # the file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        datapath = ROOT + "/Data/Credentials"
        if os.path.exists(datapath + "/token.pickle"):
            with open(datapath + "/token.pickle", "rb") as token:
                creds = pickle.load(token)
                print("Credentails: 🔐", creds)
        # if there are no (valid) credentials availablle, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    datapath + '/client_secrets_file.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # save the credentials for the next run
            with open(datapath + "/token.pickle", "wb") as token:
                pickle.dump(creds, token)
        return build('gmail', 'v1', credentials=creds)
