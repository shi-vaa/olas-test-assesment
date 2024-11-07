# OLANAS Enrollment Assesment

## Introduction

 ** Autonomous agents have a number of defining characteristics: **

  - Communicate with the environment via asynchronous messages.
  -  Display reactiveness (handling messages) and proactiveness (generating new messages based on internal state or local time).
  -  Can be thought of as representing a human, organization, or thing in a specific domain and tasks.

### Agent

- Runs a JSON RPC server
- Can establish connections through sockets
- Receives & Responds to requets using json messsage types
* Can Handle three Methods for handling requests:

1. register_handler - used to activate a new existing behaviour 
2. register_behaviour - used to register a new external handler
3. Message - used to deliver messages to external agents inbox

### Getting Started

- Setup base python environment using python3 venv

```
python3 -m venv <name of project>
```

- Activate the virtual environment as source

```
source <name of project>/bin/activate

```

- To deactivate

```
<name of project>/bin/deactivate
```

-  To Install all the necessary dependencies

```
pip3 install -r requirements.txt
```

### Run the project

- Setup the .env file
- You can rename the .sample_env to .env and add the constants to the file
- Tenderly virtual testnets can also be setup
- virtual testnet explorer used for testing https://dashboard.tenderly.co/explorer/vnet/72e9563f-e09d-4a16-802c-df2c01ffd10a

#### Starting the agents

1. Agent 1

    ``` 
    python3 app.py
    ```

2. Agent 2 
    - in a new terminal
    ```
    python3 app.py
    ```

3. Running test scripts

    - Before starting tests please ensure app is up & running

    ```
    pytest test.py --verbose

    ```

