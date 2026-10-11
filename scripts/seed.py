from app.db import initialize, seed_database

initialize(seed=False)
seed_database()
print("Seed data is ready.")
