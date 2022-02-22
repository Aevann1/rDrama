This code runs https://rdrama.net, https://pcmemes.net, and https://ruqqus.us

# Installation (Windows/Linux/MacOS)

1- Install Docker on your machine.

[Docker installation](https://docs.docker.com/get-docker/)

2- Run the following commands in the terminal:

```
git clone https://github.com/Aevann1/Drama/

cd Drama

docker-compose up
```

3- That's it! Visit `localhost` in your browser.

4- Optional: to change the domain from "localhost" to something else and configure the site settings, as well as integrate it with the external services the website uses, please edit the variables in the `env` file and then restart the docker container.