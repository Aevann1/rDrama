[![Build status](https://img.shields.io/github/workflow/status/TheMotte/rDrama/run_tests.py/frost)](https://github.com/Aevann1/rDrama/actions?query=workflow%3Arun_tests.py+branch%3Afrost)


This code runs https://rdrama.net, https://pcmemes.net, https://cringetopia.org, and https://watchpeopledie.co

# Installation (Windows/Linux/MacOS)

1- Install Docker on your machine.

[Docker installation](https://docs.docker.com/get-docker/)

2 - If hosting on localhost and/or without HTTPS, change```"SESSION_COOKIE_SECURE"``` in ```__main__.py``` to "False"

3- Run the following commands in the terminal:

```
git clone https://github.com/Aevann1/rDrama/

cd rDrama

docker-compose up
```

4- That's it! Visit `localhost` in your browser.

5- Optional: to change the domain from "localhost" to something else and configure the site settings, as well as integrate it with the external services the website uses, please edit the variables in the `env` file and then restart the docker container.
