# Mail-Client

A stand-alone application which utilizes the following two scrpts to:
| S.No | Script | Function|
| -----| -------|---------|
| 1. | `main.py`   | To fetch the emails using [google-api](https://github.com/googleapis/google-api-python-client/blob/main/docs/oauth.md) and parses them to store in SQlite3 database  |
| 2. | `search.py` | To parse `rules.json` file to process the mails based on the conditions and to perform actions such as marking read/unread, moving the emails to specific labels     |

Demo can be found [here](https://youtu.be/tb06T14JzAY)
