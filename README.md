## install
1. Install the necessary dependencies using this command
```bash
pip install -r requirements.txt
```
2. Generate a self-signed SSL certificate and key pair
```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

## Configuration
### Server
1. Obtain your openai api key from [here](https://openai.com)
2. Create a .env file in the root directory of your project.
3. Inside the .env file, set the OPENAI_API_KEY environment variable to your API key using the KEY=VALUE syntax, like so: 
```bash
OPENAI_API_KEY=<your_openai_api_key_here>
```
4. Set the remaining MySQL environment variables in the .env file as follows:
```bash
MYSQL_USER=<your_mysql_username_here>
MYSQL_PASSWORD=<your_mysql_password_here>
MYSQL_HOST=<your_mysql_host_here>
MYSQL_DATABASE=<your_mysql_database_name_here>
```
5. For Google authentication, obtain a client_id and client_secret by creating a new project in the [Google Developers Console](https://console.cloud.google.com/apis/dashboard)
6. Set the GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables in the .env file, replacing the placeholder values with your own:
```bash
GOOGLE_CLIENT_ID=<your_google_client_id_here>
GOOGLE_CLIENT_SECRET=<your_google_client_secret_here>
```
7. Save the .env file
8. 
## run
```bash
python3 app.py or flask run --cert=adhoc
```

***Tech used***
  - openai API
  - Google Cloud Console
  - html
  - css
  - javascript
  - flask
  - mysql


## credits
- [OpenAI](https://openai.com) for creating [ChatGPT](https://chat.openai.com/chat)

## 📝 License © [CyberRide](https://web.facebook.com/CyberRide/)

>This project is released under the Apache License 2.0 license.
See [LICENSE](./LICENSE) for details.
