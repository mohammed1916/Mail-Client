import base64
import os
import quopri
import re
import sqlite3
import sys


class EmailParser:
    def __init__(self, service):
        self.service = service
        self.messages = []

    def fetchStoreMessages(self, query):
        # Fetch messages matching the query
        self.messages = self.service.users().messages().list(
            userId='me', q=query).execute()
        self.store()

    def store(self):
        # Create a SQLite database and table to store email data
        dbPath = os.path.dirname(os.path.abspath(sys.argv[0])) + '/Data/DB/'
        conn = sqlite3.connect(dbPath + 'emails.db')
        c = conn.cursor()
        c.execute(
            'CREATE TABLE IF NOT EXISTS emails (id TEXT PRIMARY KEY, subject TEXT, sender TEXT, receiver TEXT, internal_date TEXT, body TEXT)')

        # Insert email data into the table
        # print("self.messages", self.messages)
        for message in self.messages['messages']:
            message_id, subject, sender, receiver, internal_date, body = self.parseData(
                message)
            # print(type(internal_date), internal_date)

            # Insert the email data into the database
            c.execute('INSERT OR REPLACE INTO emails (id, subject, sender, receiver, internal_date, body) VALUES (?, ?, ?, ?, ?, ?)',
                      (message_id, subject, sender, receiver, internal_date, body))

        # Commit changes and close the database connection
        conn.commit()
        conn.close()

    def parseData(self, message):
        message_id = message['id']
        message_data = self.service.users().messages().get(
            userId='me', id=message_id).execute()
        payload = message_data['payload']
        headers = payload['headers']

        # Extract the subject and sender email address from the message data
        subject = ''
        sender = ''
        receiver = ''
        internal_date = ''
        for header in headers:
            # print(header)
            if header['name'] == 'Subject':
                subject = header['value']
            elif header['name'] == 'From':
                sender = header['value']
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                match = re.search(email_pattern, sender)
                if match:
                    sender = match.group(0)
                else:
                    print("No email found")
                    print('header[\'value\']: ', header['value'])
            elif header['name'] == 'Delivered-To':
                receiver = header['value']
            elif header['name'] == 'Date':
                internal_date = header['value']

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

        return message_id, subject, sender, receiver, internal_date, body


"""
Sample Headers for Reference

{'name': 'Delivered-To', 'value': 'samplesoftwaredemo@gmail.com'
}
{'name': 'Received', 'value': 'by 2002:a05: 6f02: 6787:b0: 46: 4fd9:fdd with SMTP id x7csp266289rcg;        Sat,
    18 Mar 2023 03: 21: 59 -0700 (PDT)'
}
{'name': 'X-Google-Smtp-Source', 'value': 'AK7set883MyHG7fgykWP5MibhiT94lpUS/puY6Qo+owp+xWMp7A0SwWqm37sT6Cgrs3AsAlVdm1c'
}
{'name': 'X-Received', 'value': 'by 2002:a17: 90a: 77ca:b0: 23b: 4d09:c166 with SMTP id e10-20020a17090a77ca00b0023b4d09c166mr11836889pjs.4.1679134918849;        Sat,
    18 Mar 2023 03: 21: 58 -0700 (PDT)'
}
{'name': 'ARC-Seal', 'value': 'i=1; a=rsa-sha256; t=1679134918; cv=none;        d=google.com; s=arc-20160816;        b=NNumjMuTKMmwdDVvPGUmXBqzJZfnxYHZQ06qjv4meukKsIz38jNRrPl97mQQeeLK9h         9zQE+FThqoBM7xS0w7wN2tuLou1lxDqWtiTTP07/7rbFGFxlsqiRbDo1LHv4viDLW7J0         Pecc/WJuLvkk6G+oGXnpDVlSeFQ1C0BaRc19L8Ik3+ofGZaj0Qdk9OccnlqwbxN3bnsU         mXIFevjDSyvLdGGZDfTYBNqcOqKv6nikFzq3Y2fr2lG7zPBNxqQgz1kCtsxdrvDBCCd/         9W7VR/F0UREo1sBio88hs/t5ptYBjJtOc9Y8FDJfZADU8FZ8FJS6NuYrW58pHV9gzKUC         xDlw=='
}
{'name': 'ARC-Message-Signature', 'value': 'i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20160816;        h=reply-to:subject:sender:from:mime-version:date:to:dkim-signature         :message-id;        bh=n1hbHmC1mKKLxTz3++P+HbkrzKCGZWC0pSyd0mtE0Vg=;        b=Vumc/WnaFVFymU+/md5guKZo7it8HEBl80dfV4tV8xj05fWVAxAPRfx84KLqODdady         E3SYOrQthU48y4lxkze9quXSXSxAsFhmad6shGdkr3yd80FmAUZcFcwuSiXJe8Qodn21         YjJMlOUJfeVtZstrIN7gBnh+uWt/tOHU95KYmOxg2RE9fdR9XqKd2TLLdbq2afjdKBdN         3UQ25DGlSvxHNpgCAKZlyLcnA1kBLmRdMDIssMg2PLvptIRHjrrMQaNdREMmUEsNTDfL         GNd2kye5NfNQjNkeImnI8Lq6exnxlu8M6tzPbXe0jlZkvvPu2tClwNRvVEvwMF0b7UDm         o+Tw=='
}
{'name': 'ARC-Authentication-Results', 'value': 'i=1; mx.google.com;       dkim=pass header.i=@am.atlassian.com header.s=sparkpost0223 header.b=D7LB4PXY;       spf=pass (google.com: domain of no-reply@am.atlassian.com designates 192.174.81.121 as permitted sender) smtp.mailfrom=no-reply@am.atlassian.com;       dmarc=pass (p=NONE sp=NONE dis=NONE) header.from=atlassian.com'
}
{'name': 'Return-Path', 'value': '<no-reply@am.atlassian.com>'
}
{'name': 'Received', 'value': 'from mta-81-121.sparkpostmail.com (mta-81-121.sparkpostmail.com. [
        192.174.81.121
    ])        by mx.google.com with ESMTPS id u2-20020a170902bf4200b0019953ab9cf2si4592738pls.138.2023.03.18.03.21.57        for <samplesoftwaredemo@gmail.com>        (version=TLS1_2 cipher=ECDHE-ECDSA-AES128-GCM-SHA256 bits=128/128);        Sat,
    18 Mar 2023 03: 21: 58 -0700 (PDT)'
}
{'name': 'Received-SPF', 'value': 'pass (google.com: domain of no-reply@am.atlassian.com designates 192.174.81.121 as permitted sender) client-ip=192.174.81.121;'
}
{'name': 'Authentication-Results', 'value': 'mx.google.com;       dkim=pass header.i=@am.atlassian.com header.s=sparkpost0223 header.b=D7LB4PXY;       spf=pass (google.com: domain of no-reply@am.atlassian.com designates 192.174.81.121 as permitted sender) smtp.mailfrom=no-reply@am.atlassian.com;       dmarc=pass (p=NONE sp=NONE dis=NONE) header.from=atlassian.com'
}
{'name': 'Message-ID', 'value': '<641590c6.170a0220.7f101.37a3SMTPIN_ADDED_BROKEN@mx.google.com>'
}
{'name': 'X-Google-Original-Message-ID', 'value': '<272ea7b5-1a28-4c25-9ddc-a3a3655750bc--jira>'
}
{'name': 'X-MSFBL', 'value': 'NyJHAdU+3SSJdphfYWY9wfOpczpIu/9IpDCX33yUdgo=|eyJ0ZW5hbnRfaWQiOiJ hdGxhc3NpYW51cyIsInN1YmFjY291bnRfaWQiOiIwIiwiciI6InNhbXBsZXNvZnR 3YXJlZGVtb0BnbWFpbC5jb20iLCJtZXNzYWdlX2lkIjoiNjQwOWM0OTAxNTY0Y2Y yODI0MTIiLCJjdXN0b21lcl9pZCI6IjEifQ=='
}
{'name': 'DKIM-Signature', 'value': 'v=1; a=rsa-sha256; c=relaxed/relaxed; d=am.atlassian.com; s=sparkpost0223; t=1679134916; i=@am.atlassian.com; bh=n1hbHmC1mKKLxTz3++P+HbkrzKCGZWC0pSyd0mtE0Vg=; h=To:Date:Content-Type:Message-ID:From:Subject:From:To:Cc:Subject; b=D7LB4PXYaSYLoXfnA+7aRlQuULbwY5afQrlcPAFc36xx55452sOLWMLLTmTGCyZ7K\t W4vF1qZfj79VVHYsEC5tiZ4l8xVYAWDvzoyIdanmsxVA5qu25wFvS8/xKy2n1kyPjD\t 857CiB46O980ax9MAm1fcigtCiesNeVzv4F3nl4YYtdZ1aa1DRIHiM6GmNCZxhqMef\t oO39+SQQwJeOdAEGM0rbhSa2wzmEcuV8hsgaxh++EghP5/d3el5bTlYMWI/haNMgbR\t r62qNZ6mzQXY26RWvbEbnbn8g62f5Lu+aTffm/4Lpsjn/Pc7xe5VbJKrE4CnA2njcf\t fJuyqqteqTsCA=='
}
{'name': 'To', 'value': 'samplesoftwaredemo@gmail.com'
}
{'name': 'Date', 'value': 'Sat,
    18 Mar 2023 10: 21: 56 +0000'
}
{'name': 'Content-Type', 'value': 'multipart/alternative; boundary="_----3mYQqufneck6LDJsnJ/H4A===_6E/11-28269-4C095146"'
}
{'name': 'MIME-Version', 'value': '1.0'
}
{'name': 'X-Atlassian-Mail-Message-Id', 'value': '<272ea7b5-1a28-4c25-9ddc-a3a3655750bc--jira>'
}
{'name': 'X-Atlassian-Mail-Transaction-Id', 'value': 'e45ff3bb-635b-4275-814d-f752d9c240a7'
}
{'name': 'From', 'value': 'no-reply@am.atlassian.com'
}
{'name': 'Sender', 'value': 'no-reply@am.atlassian.com'
}
{'name': 'Subject', 'value': '[Important Notice
    ] Your Jira subscription is being deactivated'
}
{'name': 'Reply-To', 'value': '<no-reply@am.atlassian.com>'
}
{'name': 'Delivered-To', 'value': 'samplesoftwaredemo@gmail.com'
}
{'name': 'Received', 'value': 'by 2002:a05: 6f02: 6787:b0: 46: 4fd9:fdd with SMTP id x7csp144998rcg;        Fri,
    17 Feb 2023 10: 16: 20 -0800 (PST)'
}
{'name': 'X-Google-Smtp-Source', 'value': 'AK7set/IeL942YRAyJ8egiVe0hfouqV+CpzOzls2anfg1UHr7MkOjVaknOl6UOJ7B8Sdg6dcOpRh'
}
{'name': 'X-Received', 'value': 'by 2002:ac8: 5e54: 0:b0: 39c:da22: 47b8 with SMTP id i20-20020ac85e54000000b0039cda2247b8mr4633903qtx.1.1676657780555;        Fri,
    17 Feb 2023 10: 16: 20 -0800 (PST)'
}
{'name': 'ARC-Seal', 'value': 'i=1; a=rsa-sha256; t=1676657780; cv=none;        d=google.com; s=arc-20160816;        b=YYSJ0SCa/HjytQFSrTpVTbA2Mklq0R+ZA61bAygZREOi340C6N45my4vP7VUp5VSBG         hC9JMEcuj2CBiXqMwgF/RRE6bJP5C9kMYRHLr4UDxz7dFaRoxzwoqkaz+P5ivF6WQnzo         tV+nrCA+G0Y+jtIQaAKw9Z8S5ae5TRSO+jf36LE5Vb6+TBYP2bPHy32ClVbCR4GvW1Mi         nQIeJo0XOa5sGFexcQ99axNmm6PJjZeB9OO2kNubmwB8WyXATPMSZDf8xJaYHl2UX2Nr         ry6iC2zWXLabVxd3K/E1FeaY2ruoybFmU5pvSXJg6SNIOE0/Lu7HEIueT2vnzBA4arKh         /07w=='
}
{'name': 'ARC-Message-Signature', 'value': 'i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20160816;        h=feedback-id:message-id:list-id:reply-to:mime-version         :list-unsubscribe-post:list-unsubscribe:date:subject:to:from         :dkim-signature;        bh=bNQIX6Cibqyz1h0UBdcJtbWogGaO+/X+f6Fo3OGS5pw=;        b=PZf0KW7NjZFx1H9qVD4GAi3GD65ibFMn3m2UMmbY6cfCFtD9C17RuVxOaiOuextG6n         u11IV+p6zoC9xHlOxrtP7D8NWuXouuuzAb2Wl/iHE1xPZFj+Ojb30rXG6LWvXS+QjSoL         npYA8cQKeE5df8Cti3qsO+Ry5X0rby0GicZHpuk2hBoOzXWK+4R4nXL7VO6cnGLQEN6t         o/ldTUk2fZ4OuX7STggspWX+CDTwzh1SDZJWJy+/kRDI53XN5UNEsZvXsIB2awfQHjWy         uXpcMwLrA3sJF9B9hAR8/oNVCdqubEMXIU2Qmq+70BVpt33k8ff/GVXdasRK6Xayfsyh         18+Q=='
}
{'name': 'ARC-Authentication-Results', 'value': 'i=1; mx.google.com;       dkim=pass header.i=@e.atlassian.com header.s=200608 header.b=JkE0GZd5;       spf=pass (google.com: domain of bounce-1441644_html-1724554789-105915878-524000040-995@bounce.e.atlassian.com designates 136.147.143.2 as permitted sender) smtp.mailfrom=bounce-1441644_HTML-1724554789-105915878-524000040-995@bounce.e.atlassian.com;       dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=e.atlassian.com'
}
{'name': 'Return-Path', 'value': '<bounce-1441644_HTML-1724554789-105915878-524000040-995@bounce.e.atlassian.com>'
}
{'name': 'Received', 'value': 'from mta3.e.atlassian.com (mta3.e.atlassian.com. [
        136.147.143.2
    ])        by mx.google.com with ESMTPS id e7-20020ac84e47000000b003bd16d07e57si2229648qtw.515.2023.02.17.10.16.20        for <samplesoftwaredemo@gmail.com>        (version=TLS1_2 cipher=ECDHE-ECDSA-AES128-GCM-SHA256 bits=128/128);        Fri,
    17 Feb 2023 10: 16: 20 -0800 (PST)'
}
{'name': 'Received-SPF', 'value': 'pass (google.com: domain of bounce-1441644_html-1724554789-105915878-524000040-995@bounce.e.atlassian.com designates 136.147.143.2 as permitted sender) client-ip=136.147.143.2;'
}
{'name': 'Authentication-Results', 'value': 'mx.google.com;       dkim=pass header.i=@e.atlassian.com header.s=200608 header.b=JkE0GZd5;       spf=pass (google.com: domain of bounce-1441644_html-1724554789-105915878-524000040-995@bounce.e.atlassian.com designates 136.147.143.2 as permitted sender) smtp.mailfrom=bounce-1441644_HTML-1724554789-105915878-524000040-995@bounce.e.atlassian.com;       dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=e.atlassian.com'
}
{'name': 'DKIM-Signature', 'value': 'v=1; a=rsa-sha256; c=relaxed/relaxed; s=200608; d=e.atlassian.com; h=From:To:Subject:Date:List-Unsubscribe:List-Unsubscribe-Post:MIME-Version: Reply-To:List-ID:X-CSA-Complaints:Message-ID:Content-Type; i=info@e.atlassian.com; bh=bNQIX6Cibqyz1h0UBdcJtbWogGaO+/X+f6Fo3OGS5pw=; b=JkE0GZd5k1/Kp2FLOOVs0AYq82dwVJNHbwSay/mHSoN0egP+Vz6yVf8B70z+4zYnXz49GX7oJKsS   jtCb0sAkaQ4TDgnhzlRsZBxD1EV2WIih2rksTXeDRUbSFWg84HUljE6y+LTh5NJA1Sso03Kyz54K   IAn3oe+p/xfaj3KidpM='
}
{'name': 'Received', 'value': 'by mta3.e.atlassian.com id htv2782fmd4c for <samplesoftwaredemo@gmail.com>; Fri,
    17 Feb 2023 18: 16: 19 +0000 (envelope-from <bounce-1441644_HTML-1724554789-105915878-524000040-995@bounce.e.atlassian.com>)'
}
{'name': 'From', 'value': 'Atlassian <info@e.atlassian.com>'
}
{'name': 'To', 'value': '<samplesoftwaredemo@gmail.com>'
}
{'name': 'Subject', 'value': '(1/10) Let’s get you on board!'
}
{'name': 'Date', 'value': 'Fri,
    17 Feb 2023 12: 16: 19 -0600'
}
{'name': 'List-Unsubscribe', 'value': '<https: //click.e.atlassian.com/subscription_center.aspx?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJtaWQiOiI1MjQwMDAwNDAiLCJzIjoiMTcyNDU1NDc4OSIsImxpZCI6IjE0NDE2NDQiLCJqIjoiMTA1OTE1ODc4IiwiamIiOiI5OTUiLCJkIjoiMTAxNjYifQ.JDM4y17SmHZLn9PgHEF9h8uFRGA4EtGHCaZgmXQzVwg>, <mailto:leave-fc83157471650279717b28313958-fdeb1577776001787113787c-fe231570706d05787d1378-fe4011727164047d751070-ff581d7970@leave.e.atlassian.com>'}
    {'name': 'List-Unsubscribe-Post', 'value': 'List-Unsubscribe=One-Click'
    }
{'name': 'x-CSA-Compliance-Source', 'value': 'SFMC'
    }
{'name': 'MIME-Version', 'value': '1.0'
    }
{'name': 'Reply-To', 'value': 'Atlassian <reply-105915878-1441644_HTML-1724554789-524000040-995@e.atlassian.com>'
    }
{'name': 'List-ID', 'value': '<10991049.xt.local>'
    }
{'name': 'X-CSA-Complaints', 'value': 'csa-complaints@eco.de'
    }
{'name': 'X-SFMC-Stack', 'value': '1'
    }
{'name': 'x-job', 'value': '524000040_105915878'
    }
{'name': 'Message-ID', 'value': '<3e0344c3-8873-4f0b-9cee-79ab0c271a6e@ind1s01mta1389.xt.local>'
    }
{'name': 'Feedback-ID', 'value': '524000040: 105915878: 136.147.143.2:sfmktgcld'
    }
{'name': 'Content-Type', 'value': 'multipart/alternative; boundary="LaKVDFr7nH9A=_?:"'
    }
"""
