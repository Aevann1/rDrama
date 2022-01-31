[![Website](https://img.shields.io/website/https/rdrama.net?down_color=red&down_message=down&up_message=up)](https://www.rdrama.net) ![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/Aevann1/Drama) ![Lines of code](https://img.shields.io/tokei/lines/github/Aevann1/Drama)

# Installation

Installing Drama locally is the fastest way to get the software up and running and start tinkering under the hood.

---

# Windows/Linux/MacOS

1- Install Docker on your machine.

[Docker installation](https://docs.docker.com/get-docker/)

2- Run the following commands in the terminal:

```
git clone https://github.com/Aevann1/Drama/

cd drama

docker-compose up
```

3- That's it! Visit `localhost` in your browser.

4- Optional: to change the domain from "localhost" to something else and configure the site settings, as well as integrate it with the external services the website uses, please edit the variables in the docker-compose.yml file and then restart the docker container from inside the docker app.