#!/usr/bin/python3

import subprocess
import sys

# we want to leave the container in whatever state it currently is, so check to see if it's running
docker_inspect = subprocess.run([
            "docker",
            "container",
            "inspect",
            "-f", "{{.State.Status}}",
            "rDrama",
        ],
        capture_output = True,
    ).stdout.decode("utf-8").strip()

was_running = docker_inspect == "running"

# update containers, just in case they're out of date
if was_running:
    print("Updating containers . . .")
else:
    print("Starting containers . . .")
subprocess.run([
            "docker-compose",
            "up",
            "--build",
            "-d",
        ],
        check = True,
    )

# run the test
print("Running test . . .")
result = subprocess.run([
        "docker",
        "exec",
        "rDrama",
        "bash", "-c", "cd service && python3 -m pytest -s"
    ])

if not was_running:
    # shut down, if we weren't running in the first place
    print("Shutting down containers . . .")
    subprocess.run([
            "docker-compose",
            "stop",
        ],
        check = True,
    )

sys.exit(result.returncode)