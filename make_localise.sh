pybabel extract -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d app/translations -l de
pybabel compile -d app/translations