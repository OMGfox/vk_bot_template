# vk bot template
The simulation of booking a plane ticket

### install and running
You need to have the installed database like a postgres or sqlite3 before starting<br>
1. create settings.py file from settings_default.py and leave it in the root application directory<br>
1.1 set up the TOKEN and GROUP_ID constants in the settings.py file<br>
1.2 set up the database connection settings in settings.py, in the DB_CONFIG section<br> <a href="https://docs.ponyorm.org/firststeps.html#database-binding">check here to learn more<a>
2. create venv and install all requirements:<br>
! execute the next commands from the application directory<br>
<i># python -m venv .venv <i><br>
<i># source .venv/bin/activate <i><br>
<i># pip install -r requirements.txt <i><br>
3. starting:<br>
<i># python main.py<i><br>
