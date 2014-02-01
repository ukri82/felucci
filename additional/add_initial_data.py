import sqlite3
conn = sqlite3.connect('C:/Unni/ODESK/Felucci/web2py/applications/felucci/databases/storage.sqlite')

c = conn.cursor()

teams = [('Brazil', 'Kaka', 'Scolari', 'brazil.ico', 'a great team from earth', '0, 10, 2'),
         ('Germany', 'Kaka', 'Scolari', 'germany.ico', 'a great team from earth', '0, 10, 2'),
        ]
c.executemany('INSERT INTO teams VALUES (?,?,?,?,?,?)', teams)

