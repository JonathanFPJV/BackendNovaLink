from models import *
from database import engine, Base
import sqlalchemy

# Crear todas las tablas
Base.metadata.create_all(bind=engine)

print('✅ Base de datos creada con éxito')
print('\nTablas creadas:')

inspector = sqlalchemy.inspect(engine)
for table in inspector.get_table_names():
    print(f'  - {table}')
    
print('\n✅ Sistema listo para usar!')
