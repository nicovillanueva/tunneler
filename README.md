# Hypertunnel

## Configuration
By default, hypertunnel searches for a `config.yml` file next to it. You can set the path to a different one by the `-c` parameter.

The configuration file is made up of 2 (well, 3) sections: `tunnels` and `hops` (and `logging`)

### Tunnels/Port forwards
The tunnels are defined in the manner `<local_port>:<remote_host>:<remote_port>` much like in the SSH -L parameter, or in the SSH config file.

The remote host refers to whose `remote_port` will be exposed locally as `local_port`


## TODO:
- Randomize intermediate ports
- Clean up created ports if shit went down
