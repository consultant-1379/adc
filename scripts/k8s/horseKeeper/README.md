# Requirements

1. Python
2. The kubernetes library.

```
pip install -r requirements.txt
```


## Description:
horseKeeper is for configuring TLS certificates for Grafana elastic search datasource, the 'elastic search datasource' could be used by Grafana Dashboards for log querying 

## Benifits
Normally, we use the certificates in CNF secrets for the TLS elastic search query, but the lifetime of these certificates is only 7 days, once they are expired, we have to configure

the Grafana datasources manually again, and we have serveral CNF instances in one 5GC testing channel and more than one testing channel could be involved for 5GC testing,

that means lots of effort is needed for we do it manually, This tool could help us save it

## Usage

```pycon
horseKeeper.py -h
###################################################################################
Hi, the horseKeeper is for configuring certificates in grafana TLS elastic search 
    datasources by updating the k8s configmap & restarting the relative grafana pod.
###################################################################################
usage: Usage:

horseKeeper argument parser.

optional arguments:
  -h, --help            show this help message and exit
  --cluster CLUSTER, -e CLUSTER
                        the target k8s cluster on which the grafana is.
  --namespaces NAMESPACES [NAMESPACES ...], -n NAMESPACES [NAMESPACES ...]
                        the namespace(CNF) list from which we get the certificate data.
  --output OUTPUT, -o OUTPUT
                        (optional) the path for saving the extracted certificate files from CNF secrets.

```

#### Command example

```
seroiuts02138[07:00] ~ $ horseKeeper.py -e n99-eccd1 -n sc ccrc ccsm
###################################################################################
Hi, the horseKeeper is for configuring certificates in grafana TLS elastic search
    datasources by updating the k8s configmap & restarting the relative grafana pod.
###################################################################################
2023-02-14 07:22:18,017 INFO: Parsing secrets in namespace sc
2023-02-14 07:22:18,164 INFO: The CA certificate is saved in /tmp/n99-eccd1/sc-ca.crt
2023-02-14 07:22:18,186 INFO: The client certificate is saved in /tmp/n99-eccd1/sc-cert.pem
2023-02-14 07:22:18,187 INFO: The private key of client certificate is saved in /tmp/n99-eccd1/sc-key.pem
2023-02-14 07:22:18,187 INFO: Parsing secrets in namespace ccrc
2023-02-14 07:22:18,386 INFO: The CA certificate is saved in /tmp/n99-eccd1/ccrc-ca.crt
2023-02-14 07:22:18,407 INFO: The client certificate is saved in /tmp/n99-eccd1/ccrc-cert.pem
2023-02-14 07:22:18,407 INFO: The private key of client certificate is saved in /tmp/n99-eccd1/ccrc-key.pem
2023-02-14 07:22:18,407 INFO: Parsing secrets in namespace ccsm
2023-02-14 07:22:18,426 INFO: The CA certificate is saved in /tmp/n99-eccd1/ccsm-ca.crt
2023-02-14 07:22:18,445 INFO: The client certificate is saved in /tmp/n99-eccd1/ccsm-cert.pem
2023-02-14 07:22:18,446 INFO: The private key of client certificate is saved in /tmp/n99-eccd1/ccsm-key.pem
2023-02-14 07:22:18,506 INFO: Patch grafana datasources config map successfully!
2023-02-14 07:22:18,520 INFO: Restart pod:grafana-5dbc45df7d-lkxkb in namesapce grafana
2023-02-14 07:22:18,539 INFO: Sleep 10 seconds for new pods.
2023-02-14 07:22:28,557 INFO: The action of restart pods grafana-XXX-XXX in namespace grafana is done.
```
