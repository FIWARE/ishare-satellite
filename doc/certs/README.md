# Certificates

Manual for creating Root CA, intermediates, server/client certificates and certificate chains using `openssl`. 

This is just an example which allows to create any number of client/server certificates + private keys to be 
registered at the satellite. This also includes to create a server certificate + private key for the server 
itself. Note that each participant should have a unique EORI which is specified in the `subj` 
parameter `serialNumber` when creating the corresponding CSR.

The created root CA should be configued in the satellite `trusted_list`.


> :bulb: In case you are running on plain linux, its likely that the [default openssl.conf](openssl.cnf) does not work. Try out the [openssl.cnf-linux](./openssl.cnf-linux) instead.

## Create Root CA Certificate

File `serial` should contain:
```apache
01
```

File `index.txt` should be empty.


### Private Key

* Generate private key
```shell
mkdir private
openssl genrsa -out private/cakey.pem 4096
```


### Certificate

* Create certificate
```shell
mkdir certs
openssl req -new -x509 -days 3650 -config ./openssl.cnf -extensions v3_ca \
  -key private/cakey.pem -out certs/cacert.pem

>
-----
Country Name (2 letter code) [DE]:
State or Province Name (full name) [Berlin]:
Locality Name (eg, city) [Berlin]:
Organization Name (eg, company) [FIWARE]:
Organizational Unit Name (eg, section) []:
Common Name (e.g. server FQDN or YOUR name) []:FIWARE-CA
Email Address []:test@fiware.org
```

* Change to PEM output
```shell
openssl x509 -in certs/cacert.pem -out certs/cacert.pem -outform PEM
```

* Verify certificate
```shell
openssl x509 -noout -text -in certs/cacert.pem
```


## Create Intermediate CA Certificate

In directory `intermediate`, file `serial` should contain:
```apache
01
```

File `index.txt` should be empty.


### Private Key

* Create private key
```shell
mkdir ./intermediate/private
openssl genrsa -out ./intermediate/private/intermediate.cakey.pem 4096
```


### Certificate Signing Request

* Create CSR
```shell
mkdir ./intermediate/csr
openssl req -new -sha256 -config ./intermediate/openssl.cnf \
  -key ./intermediate/private/intermediate.cakey.pem \
  -out ./intermediate/csr/intermediate.csr.pem

>
-----
Country Name (2 letter code) [DE]:
State or Province Name (full name) [Berlin]:
Locality Name (eg, city) [Berlin]:
Organization Name (eg, company) [FIWARE]:
Organizational Unit Name (eg, section) []:
Common Name (e.g. server FQDN or YOUR name) []:FIWARE-CA_TLS
Email Address []:test@fiware.org

Please enter the following 'extra' attributes
to be sent with your certificate request
A challenge password []:
An optional company name []:FIWARE Foundation
```

### Certificate

* Create and sign intermediate CA certificate
```shell
mkdir intermediate/certs
openssl ca -config openssl.cnf -extensions v3_intermediate_ca -days 2650 -notext \
  -batch -in intermediate/csr/intermediate.csr.pem \
  -out intermediate/certs/intermediate.cacert.pem
```

* Change to PEM output
```shell
openssl x509 -in intermediate/certs/intermediate.cacert.pem -out intermediate/certs/intermediate.cacert.pem -outform PEM
```

* Verify certificate
```shell
openssl x509 -noout -text -in intermediate/certs/intermediate.cacert.pem
```

* Create Certificate Chain and verify
```shell
cat intermediate/certs/intermediate.cacert.pem certs/cacert.pem > intermediate/certs/ca-chain-bundle.cert.pem
openssl verify -CAfile certs/cacert.pem intermediate/certs/ca-chain-bundle.cert.pem
```


## Create Client Certificate

Create signed certificate for a client (e.g., a sender of requests).


### Private Key

* Generate private key
```shell
openssl genrsa -out ./client/client.key.pem 4096
```

### CSR

* Create CSR
```shell
openssl req -new -key ./client/client.key.pem -out ./client/client.csr \
  -subj "/C=DE/ST=Berlin/L=Berlin/O=FIWARE Client/CN=FIWARE-Client/emailAddress=client@fiware.org/serialNumber=EU.EORI.FIWARECLIENT"
```


### Certificate

* Create and sign client certificate
```shell
openssl x509 -req -in ./client/client.csr -CA ./intermediate/certs/ca-chain-bundle.cert.pem \
  -CAkey ./intermediate/private/intermediate.cakey.pem -out ./client/client.cert.pem \
  -CAcreateserial -days 1825 -sha256 -extfile ./client/client_cert_ext.cnf
```

* Change to PEM output
```shell
openssl x509 -in client/client.cert.pem -out client/client.cert.pem -outform PEM
```



### Verify

* Verify contents:
```shell
openssl rsa -noout -text -in ./client/client.key.pem
openssl req -noout -text -in ./client/client.csr
openssl x509 -noout -text -in ./client/client.cert.pem
```


## Create Server Certificate

Create signed certificate for a server (e.g., a receiver of requests or the satellite itself).


### Private Key

* Generate Private Key
```shell
openssl genrsa -out ./server/server.key.pem 4096
```


### CSR

* Create CSR
```shell
openssl req -new -key ./server/server.key.pem -out ./server/server.csr \
  -subj "/C=DE/ST=Berlin/L=Berlin/O=FIWARE Server/CN=FIWARE-Server/emailAddress=server@fiware.org/serialNumber=EU.EORI.FIWARESERVER"
```


### Certificate

* Create and sign server certificate
```shell
openssl x509 -req -in ./server/server.csr -CA ./intermediate/certs/ca-chain-bundle.cert.pem \
  -CAkey ./intermediate/private/intermediate.cakey.pem -out ./server/server.cert.pem \
  -CAcreateserial -days 1825 -sha256 -extfile ./server/server_cert_ext.cnf
```

* Change to PEM output
```shell
openssl x509 -in server/server.cert.pem -out server/server.cert.pem -outform PEM
```

### Verify

* Verify contents:
```shell
openssl rsa -noout -text -in ./server/server.key.pem
openssl req -noout -text -in ./server/server.csr
openssl x509 -noout -text -in ./server/server.cert.pem
```
