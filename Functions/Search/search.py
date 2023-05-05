import base64
import os
import quopri
import re
import sqlite3


class Search:
    def search_messages(service, query):
        # Fetch messages matching the query
        messages = service.users().messages().list(userId='me', q=query).execute()

        # Create a SQLite database and table to store email data
        dbPath = os.getcwd() + '/Data/DB/'
        conn = sqlite3.connect(dbPath + 'emails.db')
        c = conn.cursor()
        c.execute(
            'CREATE TABLE IF NOT EXISTS emails (id TEXT PRIMARY KEY, subject TEXT, sender TEXT, body TEXT)')

        # Insert email data into the table
        for message in messages['messages']:
            message_id = message['id']
            message_data = service.users().messages().get(
                userId='me', id=message_id).execute()
            payload = message_data['payload']
            headers = payload['headers']

            # Extract the subject and sender email address from the message data
            subject = ''
            sender = ''
            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
                elif header['name'] == 'From':
                    sender = header['value']

            # Look for text/plain and text/html body parts in the message payload
            body = ''
            for part in payload.get('parts', [payload]):
                if part.get('mimeType') == 'text/plain':
                    body = part.get('body', {}).get('data', '')
                    break
                elif part.get('mimeType') == 'text/html':
                    body = part.get('body', {}).get('data', '')
                    # Convert HTML entities to Unicode
                    body = quopri.decodestring(
                        body.encode('utf-8')).decode('utf-8')
                    # Remove HTML tags
                    body = re.sub('<[^<]+?>', '', body)
                    break

            # Decode the body content from base64
            if body:
                body = base64.urlsafe_b64decode(body).decode('utf-8')

            # Insert the email data into the database
            c.execute('INSERT OR REPLACE INTO emails (id, subject, sender, body) VALUES (?, ?, ?, ?)',
                      (message_id, subject, sender, body))

        # Commit changes and close the database connection
        conn.commit()
        conn.close()
