# rfk-bildungsplattform

## Generate graphical model overview
The applications for which an overview is generated are configured in settings.py
```
$ ./manage.py graph_models -o bildungsplattform_model.png
```

## Backup the postgres db
Assuming you have the required parameters set as env-vars

```
pg_dump > "backups/backup_$(date +'%Y-%m-%d_%H-%M-%S').sql"
```