"""
Database initialization script
Creates tables and inserts default data
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, init_database, test_connection
from database.models import Base, User, Persona, PersonaType, UserRole
from auth.authentication import AuthService
import structlog

logger = structlog.get_logger()

def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False

def create_default_user():
    """Create a default admin user for initial setup"""
    from database.connection import get_db

    auth_service = AuthService()

    with get_db() as db:
        # Check if admin user exists
        admin = db.query(User).filter(User.email == "admin@ogtool.com").first()
        if admin:
            logger.info("Admin user already exists")
            return

        # Create admin user
        admin = User(
            email="admin@ogtool.com",
            username="admin",
            password_hash=auth_service.hash_password("admin123"),  # Change this!
            full_name="OGTool Admin",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        db.commit()

        logger.info("Default admin user created (email: admin@ogtool.com, password: admin123)")
        logger.warning("IMPORTANT: Change the default admin password immediately!")

def create_default_personas():
    """Create default persona templates"""
    from database.connection import get_db
    from services.ai_response_generator import PERSONA_TEMPLATES

    with get_db() as db:
        # Get admin user
        admin = db.query(User).filter(User.email == "admin@ogtool.com").first()
        if not admin:
            logger.error("Admin user not found")
            return

        # Check if personas already exist
        existing = db.query(Persona).filter(Persona.user_id == admin.id).count()
        if existing > 0:
            logger.info(f"Personas already exist for admin user ({existing} found)")
            return

        # Create personas from templates
        for key, template in PERSONA_TEMPLATES.items():
            persona = Persona(
                user_id=admin.id,
                name=template["name"],
                type=template["type"],
                description=f"Default {template['name']} persona",
                voice_tone=template["voice_tone"],
                background=template["background"],
                expertise=template["expertise"],
                communication_style=template["communication_style"],
                values=template["values"],
                greeting_template=template.get("greeting_template"),
                closing_template=template.get("closing_template"),
                max_response_length=500,
                include_call_to_action=True,
                include_credentials=False,
                is_active=True,
                is_default=(key == "founder")  # Make founder the default
            )
            db.add(persona)

        db.commit()
        logger.info(f"Created {len(PERSONA_TEMPLATES)} default personas")

def initialize_database():
    """Initialize the database with tables and default data"""
    logger.info("Starting database initialization...")

    # Test connection
    if not test_connection():
        logger.error("Cannot connect to database")
        return False

    # Create tables
    if not create_tables():
        return False

    # Create default data
    create_default_user()
    create_default_personas()

    logger.info("Database initialization completed successfully")
    return True

if __name__ == "__main__":
    # Allow running this script directly
    import argparse

    parser = argparse.ArgumentParser(description="Initialize OGTool database")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables")
    args = parser.parse_args()

    if args.reset:
        logger.warning("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped")

    success = initialize_database()

    if success:
        print("\n✅ Database initialized successfully!")
        print("\n📝 Default credentials:")
        print("   Email: admin@ogtool.com")
        print("   Password: admin123")
        print("\n⚠️  IMPORTANT: Change the default password immediately!")
    else:
        print("\n❌ Database initialization failed. Check the logs for details.")
        sys.exit(1)