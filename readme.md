# Installation

Installing Drama locally is the fastest way to get the software up and running and start tinkering under the hood.

---

# Windows

1- Install Docker on your machine.

[Docker installation for Windows](https://docs.docker.com/docker-for-windows/install/)

2- Download Drama into your machine by running this command.

```
git clone https://github.com/Aevann1/Drama/
```

3- Press shift+right click inside the Drama code folder and run PowerShell. Then in PowerShell, run the following command:

```
docker-compose up
```

4- That's it! Visit `localhost` in your browser.

5- Optional: to configure the site settings and successsfully integrate it with the external services we use (hcaptcha, cloudflare, discord, giphy, mailgun, pusher, imgur, and youtube), please edit the variables in the docker-compose.yml file.

---

# Linux

1- Download Drama into your machine by running this command.

```
git clone https://github.com/Aevann1/Drama/ /drama
```

2- Navigate to `/drama`

```
cd /drama
```

3- run the following command:

```
source setup
```

4- That's it. Visit `localhost` in your browser.


5- Optional: to configure the site settings and successsfully integrate it with the external services we use (hcaptcha, cloudflare, discord, giphy and mailgun), please run this command and edit the variables:

```
nano /drama/docker-compose.yml
```
