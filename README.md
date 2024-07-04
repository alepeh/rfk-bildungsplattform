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

 curl -X POST https://api.scaleway.com/transactional-email/v1alpha1/regions/fr-par/emails -H "X-Auth-Token: f955bec3-ecfe-457d-909d-d2fbe0e28bab" -d '{"from": {"email": "noreply@rauchfangkehrer.or.at", "name": "Rauchfangkehrer Bildungsplattform"}, "to": [{"name": "Alice", "email": "alexander@pehm.biz"}], "subject": "Erinnerung: Schulungstermin am 2027-03-01 07:00:00+00:00 zum Thema Testschulung", "text": "Textyasdadadadadaddadada", "html": "Test  dddssddf +fdsdr", "project_id": "03bc621b-579e-4758-8b97-87f6406b2a38"}'