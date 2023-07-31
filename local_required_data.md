# All Environment Variables For Repository #
The following is all the required environment variables needed for full functionally of the program in a shell script format:
```sh
export GM_TK="" # GroupMe API Token
export USER_ID="" # GroupMe User ID For Account The Bot Will Run Under
export GROUP_ID="" # ID For Desired Group Chat
export BOT_ID="" # ID Of Bot

# Variables Needed For Some Bot Commands
export STORE_NUMBER="" # Phone Number For Workplace
export DAY1_URL="" # Link To Day 1 Coaching Guide
export POLICY_MANUAL_URL="" # Link To Store Policy Manual

# Variables Needed For Google Sheets Training Schedule
export SPREADSHEET_LINK="" # Link To View The Schedule
export SPREADSHEET_ID="" # ID To Google Sheet
```

# Admin Whitelist #
Within the GroupMe-Chatbot directory, you will need a whitelist JSON file containing the GroupMe ID's and the persons name for reference in order to successfully allow that person to use the admin commands found within the bot commands. The following file should look like:
```json
{
    "GROUPMEID": "PERSON'S NAME",
    "GROUPMEID": "PERSON'S NAME",
    "GROUPMEID": "PERSON'S NAME",

}
```

# Google Service Account Key #
The JSON file containing the google service account you will use to interact with the google sheets training schedule. The following format should look like:
```json
{
  "type": "service_account",
  "project_id": "PROJECT_ID",
  "private_key_id": "KEY_ID",
  "private_key": "-----BEGIN PRIVATE KEY-----\nPRIVATE_KEY\n-----END PRIVATE KEY-----\n",
  "client_email": "SERVICE_ACCOUNT_EMAIL",
  "client_id": "CLIENT_ID",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://accounts.google.com/o/oauth2/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/SERVICE_ACCOUNT_EMAIL"
}
```

For more information about Google Service Accounts visit [here](https://cloud.google.com/iam/docs/service-account-overview).