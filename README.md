# Script Scoring Api

**The script apy.py launches API scoring service .**

**To get the result, you need to send a valid JSON in a POST request of a certain format to http://127.0.0.1:8080/method/**

**JSON request format:**
```
{"account": "<partner company name>", "login": "<user name>", "method": "<method name>", "token": "
<authentication token> "," arguments ": {<dictionary with arguments to the called method>}}
```

**request requirements:**
* account - string, optionally, may be empty
* logi n - the string must be empty
* method - the string must be empty
* token - the string must be empty
* arguments - a dictionary (scope in terms of json), may be empty
