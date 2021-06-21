# monstar

## Dependencies
- bash
- kubernetes cluster v1.14+
- helm3 client
  This installer uses helm3 client.
- storage with the right storage class name
- python3

## Features
- install a group of application with a menifest file 
 - support types: armada, helmrelease (fluxcd), decapod (TACO)
 - main purpose: install Logging/Monitoring/Alerting (Monstar) softwares
- install exporters
 - node-exporter, k8s-exporter, ceph-exporter, ....
- register monitoring features for your applications based on http(s), grpc,...
- change configuration to collect (in case of using the [hanu-reference](https://github.com/openinfradev/decapod-site/tree/main/hanu-reference))
 - logs
 - metrics

## Configuration
- 

# Quick Start

## Installer
```
> git clone https://github.com/intelliguy/monstar.git
> cd monstar/installer
> chmod 755 installer-linux
```
### Option 1
Using your manifest
```
> ./intaller-linux -m [YOUR_MANIFEST_FILE]
```

### Option 2
Using example
```
> sed -i ’s/local-path/[YOUR_STORAGE_CLASS]/g’ lma-manifest.yaml
> sed -i ’s/cluster.local/[YOUR_CLUSTER_NAME]/g’ lma-manifest.yaml
> ./intaller-linux -m lma-manifest.yaml
```