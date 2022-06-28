[![Build status](https://img.shields.io/github/workflow/status/TheMotte/rDrama/run_tests.py/frost)](https://github.com/Aevann1/rDrama/actions?query=workflow%3Arun_tests.py+branch%3Afrost)


This code runs https://rdrama.net, https://pcmemes.net, https://cringetopia.org, and https://watchpeopledie.co

# Installation (Windows/Linux/MacOS)

1- Install Docker on your machine.

[Docker installation](https://docs.docker.com/get-docker/)

2- Run the following commands in the terminal:

```
git clone https://github.com/Aevann1/rDrama/

cd rDrama

docker-compose up
```

3- That's it! Visit `localhost` in your browser.

4- Optional: to change the domain from "localhost" to something else and configure the site settings, as well as integrate it with the external services the website uses, please edit the variables in the `env` file and then restart the docker container.

------

For returning contributors, we have noticed the following issues (if you can help fix them, we will be very grateful!):

1. Docker doesn't know when we add a new Python dependency, `docker-compose build` is needed.
2. DB schema changes are not applied automatically, the easiest way to deal with that is to delete the entire environment from the Docker GUI and do `docker-compose up`. Also wait five minutes for a "sneed" commit from Aevann meaning that the sql file was regenerated.
3. Old authorization cookies from the previous instance cause a weird 404 error, clear cookies for localhost to fix.
