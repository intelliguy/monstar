# monstar

## Dependencies
- bash
- kubernetes cluster v1.14+
- helm3 client
  This installer uses helm3 client.
- storage with the right storage class name
- python3

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