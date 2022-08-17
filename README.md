# ishare-satellite

Simple implementation of an iSHARE satellite trust anchor.

It is based on Python Flask using gunicorn and runs completely stateless. 
It is configured with a static configuration file.

> :information_source:  
> This implementation of the iSHARE Satellite is only meant for testing and demonstration purposes. 
> It is not possible to change participants or trusted CAs in a running instance. It is 
> not recommended to be used in production environments. 


## Usage

Requirements:
* python >= 3.7
* [./requirements.txt](./requirements.txt)

Required python modules can be installed with 
```shell
pip install -r requirements.txt
```



### Configuration

The lists of trusted root CAs and data space participants are configured via a static 
`yaml` file. Furthermore, the satellite ID, private key, and certificates can 
be configured. An example of the configuration file can be found 
at [./config/satellite.yml](./config/satellite.yml).  
Make sure to fill this configuration file before running the satellite.

Satellite private key and certificates can be also set via ENVs, e.g., to be able 
to provide those as `Secret` in Kubernetes environments. The ENVs would override the value set 
in the configuration file.

Further ENVs control the execution of the satellite. Below is a list of the supported ENVs:

| ENV                                    | Default      | Description |
|:---------------------------------------|:------------:|:------------|
| SATELLITE_PORT                         | 8080         | Listen port |
| SATELLITE_GUNICORN_WORKERS             | 4            | Number of workers that should be created |
| SATELLITE_MAX_HEADER_SIZE              | 32768        | Maximum header size in bytes |
| SATELLITE_LOG_LEVEL                    | 'info'       | Log level |
| SATELLITE_RESPONSE_TOKEN_DURATION      | 30           | JWT expiration duration (in s) of response tokens, besides the access token |
| SATELLITE_ACCESS_TOKEN_DURATION        | 3600         | Access token expiration duration (in s) |
| SATELLITE_FINGERPRINT_ENCODING         | 'UTF-8'      | Encoding of the certificate fingerprint for the trusted list |
| SATELLITE_MAX_PARTIES_PER_PAGE         | 10           | Maximum of parties per page |
| SATELLITE_SUBJECT_ENCODING             | 'UTF-8'      | Encoding of certificate subject names |
| SATELLITE_X5C_ENCODING                 | 'UTF-8'      | Encoding of x5c certificates in JWTs |
| SATELLITE_AUTHORIZATION_HEADER         | 'Authorization' | Header name where to expect access_token |
| SATELLITE_KEY                          |              | Satellite private key provided as ENV (compare to [config/satellite.yml](./config/satellite.yml#L4)) |
| SATELLITE_CERTS                        |              | Satellite certificate chain provided as ENV (compare to [config/satellite.yml](./config/satellite.yml#L10)) |



### Run

After placing a configuration file at `config/satellite.yml`, the satellite can be started with 
```shell
bin/run.sh
```

A Dockerfile is provided to build a docker image. Releases automatically create Docker images 
at [DockerHub](https://hub.docker.com/repository/docker/fiware/ishare-satellite).

Using Docker, the satellite can be run with:
```shell
docker run --rm -p 8080:8080 -v $PWD/config/satellite.yml:/var/satellite/config/satellite.yml fiware/ishare-satellite
```


## Endpoints

The satellite is providing the following endpoints:
* `/token`: For retrieving an access token
* `/versions`: Gives information about API version
* `/trusted_list`: Gives trusted list of CAs
* `/parties`: Gives information about data space participants


## Tests

Tests can be run with `pytest` via
```shell
pytest
```

or using the created Docker image with
```shell
docker run --rm -it fiware/ishare-satellite pytest
```
