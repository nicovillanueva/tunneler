# Hypertunnel

## Configuration
By default, hypertunnel searches for a `config.yml` file next to it. You can set the path to a different one by the `-c` parameter.

The configuration file is made up of 2 (well, 3) sections: `tunnels` and `hops` (and `logging`)

### Tunnels/Port forwards
The tunnels are defined in the manner `<local_port>:<remote_host>:<remote_port>` much like in the SSH -L parameter, or in the SSH config file.

The remote host refers to whose `remote_port` will be exposed locally as `local_port`

## Configuracion
En la carpeta `src/`, hay un archivo `config.yml` donde se configuran todos los saltos que se van a usar, y los puertos que se van a usar a traves de los tuneles.

Si se quiere usar otro archivo de configuración, se puede usar el parámetro `-c` (o `--config`)

### Tuneles/Port forwards
En la seccion `tunnels` del yml, se configuran los puertos de la siguiente manera: `<puerto_local>:<host_remoto>:<puerto_remoto>`

El puerto local es como se verá el puerto una vez conectado. El host remoto, es a donde se va a conectar el último salto. Y el puerto remoto es el puerto del host remoto que queremos ver desde nuestra máquina.

Ejemplo: Si ponemos `8081:host:80`, una vez que se llegue a la última conexión, se va a exponer localmente como `localhost:8081`, a lo que se vea como `host:80` desde el último salto.

Desde ya tener en cuenta no pisar puertos locales.

### Hops
Saltos entre conexiones. Primero se conecta al primero de la lista; de ahí, al segundo; de ahí, al siguiente; etc. Se van propagando los puertos que se configuraron previamente en `tunnels`

#### Datos de conexión
Sí o sí se debe contar con el `host` y `user`. Luego, bajo `auth` puede haber `password` o `key`.

En caso de conectarnos al host mediante key SSH, poner el path (relativo o absoluto, no usar variables de entorno, pero se puede usar `~`). Si es una password, ponerla entre comillas.

## Instalación
### Requerimientos
- Python 3
- Pip
- SSH

### Dependencias
Si se lo quiere correr localmente, se necesitan instalar un par de dependencias, que están en `src/requirements.txt`.

Para instalarlas: `pip install -r src/requirements.txt`

Recomendable usar virtualenv, sino correr el `pip install` con `sudo`

## Docker
También se lo puede correr con Docker. Aunque requiere acceso a la red del host.

### Issues
Todo lo que haga referencia a un archivo (léase, `config.yml` o key SSH) tiene que manejarse con volúmenes.

En el ejemplo de abajo, se usa la key SSH en el home del usuario, y comparte con el container (como el config dice `~/.ssh/mykey`, el container puede usarla). Lo mismo el `config.yml`: El container comparte el config que está en la carpeta `src/`

Por facilidad, si se quiere usar un archivo de configuracion que no sea `config.yml`, sobreescribir el default con otro custom: `-v $(pwd)/src/redbee.yml:/data/config.yml:ro`

### Build
`docker build -t tunneler .`
### Run
    docker run -ti -v $HOME/.ssh/automation_id_rsa:/root/.ssh/automation_id_rsa:ro \
                   -v $(pwd)/src/config.yml:/data/config.yml:ro \
                   --rm --net=host tunneler
