<p align="center">
  <img src="HEXOGEN.png" alt="hexogen-logo" height="120px"/>
  <br>
  <em>Hexogen is an HAProxy configuration generator<br />
      to help dev/sec/ops teams deploy HAProxy configuration file.</em>
  <br>
</p>

The contract:

- DEV teams describe via a simple YAML file and in a realy easy way HOW TO and WHAT SHOULD BE load balanced
- OPS teams maintain HAProxy templates using the YAML file owned by DEV teams
- SEC teams enrich HAPRoxy templates to secure API or Web applications

And everything can be stored in GiT.

When we have many applications to load balance, an easy way to handle it is to use a **wildcard DNS record** owned by HAProxy.
Hexogen will generate a **host map file** and HAProxy will use it to determine which backend should by used acconrdingly to the frontend section:

```
frontend http_default
    bind *:8080 
    use_backend %[req.hdr(host),lower,map_dom(/etc/haproxy/maps/hosts.map,be_default)]
```

For exemple, a "myapplication" entry in the YAML configuration file will be accessed with this url : http://myappplication.mydomainname.ch


## The YAML configuration file for DEV Teams

The YAML configuration file is a set of applications that need to be load balanced. Each application can be configured with these keys:

| Key   | Default value | Type | Sample | Description |
| ------|-----|-------|-----------|------------------------|
| balance |roundrobin|string|balance: leastconn| Load balancing Algorithm (see https://www.haproxy.com/blog/fundamentals-load-balancing-and-the-right-distribution-algorithm-for-you). |
| cache |false|boolean|cache: true| cache backend response. |
| checkinter |2|integer|checkinter: 2|The "checkinter" parameter sets the interval between two consecutive health checks to N seconds. If left unspecified, the delay defaults to 2s.  |
| checkfall |3|integer|checkfall: 3|The "checkfall" parameter states that a server will be considered as dead after N consecutive unsuccessful health checks.  |
| checkrise |2|integer|checkrise: 2|The "checkrise" parameter states that a server will be considered as operational after N consecutive successful health checks. |
| checkurl |-|string|checkurl: /checkme| The health check URL to validate that a backend is up and running. |
| group |-|string|default: securedapi| Define an application group. |
| maintenance |false|boolean|default: false| Display a maintenance site in a case of a maintenance. |
| persist |false|boolean|persists: true| Implement sticky sessions with the client’s IP. |
| security |-|string|security: owasp-api| Identify which OWASP level is needed for security headers. |
| ssl |false|boolean|ssl: true| Set it to true if the backend is using HTTPS. |
| urls | - | array of strings | host1:80 | A list of hosts to load balance. | 

A sample YAML file can be found [here](./sample/test.yaml)

## HAProxy templates using Mako technology

To generate the HAProxy configuration we are using Mako template library. The Mako documentation can be found here: https://www.makotemplates.org/.

**Hexogen** uses only 2 variables in each template: 
- **config** : the YAML config file 
- **domainname** : the domain name for which you want to generate a configuration file.

To iterate the configuration file, we just add this code in your template: 

`
% for host in config:
`

And then, to access the configuration YAML data:

```
config[host]['security']
config[host]['cache']
config[host]['checkurl']
config[host]['persist']
config[host]['checkinter']
config[host]['checkfall']
config[host]['checkrise']
config[host]['ssl']
config[host]['group']
```

The url field is an array that we can iterate like this:
```
% for back in config[host]['urls']:
```

## How to use Hexogen with Docker

Hexogen Docker image is an alpine rootless based image: nexsoltech/hexogen:latest

Hexogen uses 4 environment variables:

- CONFIG_FILE : the YAML configuration file
- TEMPLATE_FILE : the mako template
- OUTPUT_PATH : the output path where the HAPRoxy configuration file and the host map file will be generated
- DOMAIN_NAME : the DNS Domain name to use

A sample folder with a YAML configuration file and a Mako template is provided in this repository 

Just try it out!

```
mkdir -p ./output

docker run -e CONFIG_FILE=/config/test.yaml \
           -e TEMPLATE_FILE=/config/template.mako \
           -e OUTPUT_PATH=/output/ \
           -e DOMAIN_NAME=localdomain \
           -v ./sample:/config  \
           -v ./output:/output  \
           nexsoltech/hexogen:latest
```

## How to run HAProxy with Hexogen configuration files

Our configuration files are generated, let's run HAProxy to use them

For demo purposes, we will use "localdomain" as the domain name.
In the host config (/etc/hosts), we add the following entries:

```
127.0.0.1       secpgrestcached.localdomain
127.0.0.1       secpgrest.localdomain
127.0.0.1       pgrest.localdomain
```

And then run the docker-compose.yml containing a "demo-api" container base on PostgREST.

```
docker-compose up -d
```

We can now access http://secpgrestcached.localdomain/, http://secpgrest.localdomain/ or http://pgrest.localdomain/

The first one is secured with HAProxy cache, the second is secured with no cache, the third is not secured and doesn't use any cache.

The nginx container can be used when the "maintenance" mode is activated in the YAML file. Configure it to display a maintenance page.



