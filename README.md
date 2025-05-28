# Mike's Cool Action Provider Example

## Prerequisites

> IMPORTANT❗:
>
> The following packages were installed using Mac OSX. If you are using a different
> operating system you will need to adapt the steps to fit your needs.

These packages must be installed on the machine prior to running the project.
An installation link has been provided to each of them.

* [uv][uv-install]
* [jq][jq-install]
* [ngrok][ngrok-install]

## Quick Start

1. Install the project dependencies using the `uv` python package manager.

   ```shell
   uv sync
   ```

2. Create a Globus Project, Credentials, and Scope using the included script:

   > IMPORTANT❗: Replace `<ProjectName>` with your project name.

   ```shell
   ./scripts/create_globus_creds.sh <ProjectName>
   ```

   Example:

   ```shell
   ./scripts/create_globus_creds.sh "Mike's Cool Action Provider"
   ```

   Ensure a `local.env` was generated and exists in the root project directory.

   Alternatively, if you already have Globus credentials copy the example file
   `local.example.env` and fill in the values.

   > IMPORTANT❗: If you aren't running the script to create the project credentials
     and scope ensure you've created a scope for your client using the
     [Set Up an Action Provider in Globus Auth][setting-up-auth] guide.

   ```shell
   cp local.example.env local.env
   ```

3. Run the project with the following command:

   ```shell
   uv run flask run --host localhost --port 5001
   ```

   Example Output:
   ```shell
   [2024-12-16 16:34:47,108] INFO in apt_blueprint: Initializing AuthStateBuilder for client 3232xxxx-xxxx-xxxx-xxxx-xxxxd419f6b and secret ***xxxxx
    * Debug mode: on
   WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
    * Running on http://localhost:5001
   Press CTRL+C to quit
    * Restarting with stat
   [2024-12-16 16:34:47,312] INFO in apt_blueprint: Initializing AuthStateBuilder for client 3232xxxx-xxxx-xxxx-xxxx-xxxxd419f6b and secret ***xxxxx
    * Debugger is active!
    * Debugger PIN: 103-387-468
   ```

4. In a separate terminal, run the following `ngrok` command:

   ```shell
   ngrok http http://localhost:5001
   ```
   The ngrok application will provide a public url that will tunnel traffic
   to your local machine at the same address that the Flask application is listening.

   Note the `Forwarding` address provided in the output as it will be
   used in the next step.

   Example Output:

   ```
   Session Status                online
   Account                       Bob (Plan: Free)
   Version                       3.18.2
   Region                        United States (us)
   Latency                       42ms
   Web Interface                 http://127.0.0.1:4040
   Forwarding                    https://3a5e-74-193-31-82.ngrok-free.app -> http://localhost:5000
   ```


5. In a separate terminal, run the `create_and_start_flow.sh` script to create a Flow
   that uses the `Forwarding` address provided by ngrok in the previous command.

   ```shell
   uv run ./scripts/create_flow.sh <Forwarding>
   ```

   Example:
    ```shell
   uv run ./scripts/create_and_start_flow.sh https://3a5e-74-193-31-82.ngrok-free.app
   ```

6. Notice in the terminal started above that the Flask web application logged the calls
   made to the the Action Provider.

   ```shell
   127.0.0.1 - - [16/Dec/2024 16:56:24] "GET /apt HTTP/1.1" 200 -
   127.0.0.1 - - [16/Dec/2024 16:56:45] "GET /apt HTTP/1.1" 200 -
   127.0.0.1 - - [16/Dec/2024 16:56:46] "POST /apt/run HTTP/1.1" 202 -
   127.0.0.1 - - [16/Dec/2024 16:56:50] "GET /apt/063bb012-c2a3-4632-963c-17410b663090/status HTTP/1.1" 200 -
   127.0.0.1 - - [16/Dec/2024 16:56:54] "GET /apt/063bb012-c2a3-4632-963c-17410b663090/status HTTP/1.1" 200 -
   127.0.0.1 - - [16/Dec/2024 16:57:08] "GET /apt/063bb012-c2a3-4632-963c-17410b663090/status HTTP/1.1" 200 -
   ```

## Management Commands

Run the following commands with `uv run manage.py <command>`:

`list-routes` - Used to list all the routes provided by the action provider.


## Action Provider Routes

| Function                | Methods          | Path                                             |
|-------------------------|------------------|--------------------------------------------------|
| static                  | HEAD,GET,OPTIONS | /static/<path:filename>                           |
| apt.action_introspect   | HEAD,GET,OPTIONS | /apt/                                            |
| apt._action_status      | HEAD,GET,OPTIONS | /apt/<string:action_id>/status                   |
| apt._action_cancel      | POST,OPTIONS     | /apt/<string:action_id>/cancel                   |
| apt.action_status       | HEAD,GET,OPTIONS | /apt/actions/<string:action_id>                  |
| apt.action_cancel       | POST,OPTIONS     | /apt/actions/<string:action_id>/cancel           |
| apt.action_enumerate    | HEAD,GET,OPTIONS | /apt/actions                                      |
| apt._action_run         | POST,OPTIONS     | /apt/run                                          |
| apt.my_action_run       | POST,OPTIONS     | /apt/actions                                      |
| apt.my_action_release   | POST,OPTIONS     | /apt/<string:action_id>/release                   |
| apt.my_action_release   | DELETE,OPTIONS   | /apt/actions/<string:action_id>                   |
| apt.my_action_log       | HEAD,GET,OPTIONS | /apt/<string:action_id>/log                       |
| apt.my_action_log       | HEAD,GET,OPTIONS | /apt/actions/<string:action_id>/log               |


[uv-install]: https://github.com/astral-sh/uv?tab=readme-ov-file#installation
[jq-install]: https://jqlang.github.io/jq/download/
[globus-cli-install]: https://docs.globus.org/cli/
[ngrok-install]: https://download.ngrok.com/mac-os
[setting-up-auth]: https://action-provider-tools.readthedocs.io/en/latest/setting_up_auth.html
