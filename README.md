# Script Scoring Api

**The script apy.py launches API scoring service .**

The necessary libraries for the work of the script are saved in a file requirement.txt

## Files
```buildoutcfg
apy.py
requirement.txt
score_api.cfg
scoring.py
store.py
```
Run the following command to install
```buildoutcfg
 pip freeze > requirements.txt
```
## Running

* run with default parameters from the terminal
```
python3 api.py
```

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

####Field Arguments
* phone - a line or number, 11 in length, starts with 7, optionally, can be empty
* email - a string that has @, optionally, may be empty
* fi rst_name - string, optionally, may be empty
* last_name - string, optionally, may be empty
* birthday - date in DD.MM format. YYYY, with which no more than 70 years have passed, optionally, may be empty
* gender - number 0, 1 or 2, optionally, may be empty

#####OR

* client_id s - array of number, certainly not empty
* date - date in DD.MM format. YYYY, optionally, may be empty

request example:
```buildoutcfg
curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method":
"online_score", "token":
"55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd
"arguments": {"phone": "79175002040", "email": "otus@otus.ru", "first_name": "Alexey", "last_name":
"Ivanov", "birthday": "01.01.1990", "gender": 1}}' http://127.0.0.1:8080/method/
```
or
```buildoutcfg
curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "admin", "method":
"clients_interests", "token":
"d3573aff1555cd67dccf21b95fe8c4dc8732f33fd4e32461b7fe6a71d83c947688515e36774c00fb630b039fe2223c991f045f13f240913860502
"arguments": {"client_ids": [1,2,3,4], "date": "20.07.2017"}}' http://127.0.0.1:8080/method/
```

response example:
```buildoutcfg
{"code": 200, "response": {"score": 5.0}}
```
or
```buildoutcfg
{"code": 200, "response": {"1": ["books", "hi-tech"], "2": ["pets", "tv"], "3": ["travel", "music"], "4":
["cinema", "geek"]}}
```

## Tests

For testing, the unittest library is used.
Test files are not in the directory /tests
* unit test are located in the directory /tests/unit
###### running:
```buildoutcfg
python -m unittest discover -s tests/unit
```
* unit integration tests are located in the directory /tests/integration
```buildoutcfg
python -m unittest discover -s tests/integration
```