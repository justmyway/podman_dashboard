# Setup the monitoring environment

`podman machine init`
`podman machine start`
`podman compose -f docker-compose.yml up`

```
curl -X POST -H "Content-Type: application/json" -d '{
    "name":"Influxdb",
    "type":"influxdb",
    "url":"http://influxdb:8086",
    "access":"proxy",
    "isDefault":true,
    "database":"local_influx_db",
    "jsonData": {
        "httpMode": "POST",
        "timeInterval": "1m",
        "version": "Flux",
        "organization": "home",
        "defaultBucket": "home",
        "token": "<toke>"
    }
}' http://admin:admin@localhost:3000/api/datasources
```


pip install -r requirements.txt


podman stop $(podman ps -a -q)
podman rm $(podman ps -a -q)
podman rmi $(podman images -q)
podman volume rm $(podman volume ls -q)

