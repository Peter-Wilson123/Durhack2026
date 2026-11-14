from app import app
from discovery import get_or_create_tags
from interests import seed_taxonomy
from models import (
    ChatRoom,
    Connection,
    DirectMessage,
    Interest,
    RoomMessage,
    User,
    UserInterest,
    db,
)

# IMPORTANT THIS IS NOT MEANT TO BE RUN


def seed_database():
    with app.app_context():
        # Reset tables so running seed.py multiple times never creates duplicates
        db.drop_all()
        db.create_all()

       
        # -------------------------------------------------------------------
        # 2. Users (All passwords set to: password123)
        # -------------------------------------------------------------------
        alex = User(
            username="alex",
            display_name="Alex Mercer",
            email="alex@uni.ac.uk",
            bio="First-year CS student trying to find people who like weird hobbies.",
        )
        alex.set_password("password123")

        maya = User(
            username="maya",
            display_name="Maya Lin",
            email="maya@uni.ac.uk",
            bio="Botany nerd, darkroom tinkerer, and second-hand bookshop regular.",
        )
        maya.set_password("password123")

        liam = User(
            username="liam",
            display_name="Liam O'Connor",
            email="liam@uni.ac.uk",
            bio="Weekend trail runner and analog printmaker.",
        )
        liam.set_password("password123")

        priya = User(
            username="priya",
            display_name="Priya Nair",
            email="priya@uni.ac.uk",
            bio="Collecting obscure translated novellas and mechanical keyboards.",
        )
        priya.set_password("password123")

        sam = User(
            username="sam",
            display_name="Samira Vance",
            email="sam@uni.ac.uk",
            bio="Horology enthusiast and student radio host.",
        )
        sam.set_password("password123")

        db.session.add_all([alex, maya, liam, priya, sam])
        db.session.flush()

        # -------------------------------------------------------------------
        # 3. Categories and tags (from taxonomy.py)
        # -------------------------------------------------------------------
        seed_taxonomy()

        # -------------------------------------------------------------------
        # 4. Interests (Standard + User-Created)
        # -------------------------------------------------------------------
        # Standard interests (created_by_user_id = None)
        i_mycology = Interest(
            interest_name="Urban Mycology & Spore Printing",
            description="Identifying wild fungi in city parks and making spore prints on glass.",
            tags=get_or_create_tags(["mycology", "foraging", "botany", "nature"]),
            created_by_user_id=None,
        )
        i_cyanotype = Interest(
            interest_name="Cyanotype Sun Printing",
            description="19th-century Prussian blue photographic printing using UV sunlight.",
            tags=get_or_create_tags(["printmaking", "film photography", "botany"]),
            created_by_user_id=None,
        )
        i_translated_novellas = Interest(
            interest_name="1970s Japanese Surrealist Novellas",
            description="Reading and discussing short, dreamlike post-war fiction.",
            tags=get_or_create_tags(["fiction", "japanese", "reading", "translation"]),
            created_by_user_id=None,
        )
        i_watchmaking = Interest(
            interest_name="Mechanical Watch Escapement Tuning",
            description="Disassembling and regulating vintage wind-up wristwatches.",
            tags=get_or_create_tags(["watchmaking", "mechanics", "restoration", "craftsmanship"]),
            created_by_user_id=None,
        )
        i_field_recording = Interest(
            interest_name="Hydrophone & Contact-Mic Field Recording",
            description="Capturing underwater river sounds and bridge vibrations.",
            tags=get_or_create_tags(["field recording", "music production", "nature"]),
            created_by_user_id=None,
        )

        # User-created interest (related to others through shared tags)
        i_sundials = Interest(
            interest_name="Medieval Sundial Restoration",
            description="Mapping and calculating angles on historic stone church sundials.",
            tags=get_or_create_tags(["medieval history", "heritage", "restoration", "astronomy"]),
            creator=alex,
        )

        db.session.add_all([
            i_mycology,
            i_cyanotype,
            i_translated_novellas,
            i_watchmaking,
            i_field_recording,
            i_sundials,
        ])
        db.session.flush()

        # -------------------------------------------------------------------
        # 5. UserInterests (Designed to showcase both recommendation rules)
        # -------------------------------------------------------------------
        user_interests = [
            # Alex has 1 standard interest (Mycology) and 1 user-created (Sundials)
            UserInterest(
                user_id=alex.user_id,
                interest_id=i_mycology.interest_id,
                experience_level="Curious",
                personal_note="Looking for weekend foraging walks near campus!",
            ),
            UserInterest(
                user_id=alex.user_id,
                interest_id=i_sundials.interest_id,
                experience_level="Deep Dive",
                personal_note="Founded this group after spotting three worn sundials in town.",
            ),
            # Maya & Liam are Alex's friends who share Mycology AND both do Cyanotype
            UserInterest(
                user_id=maya.user_id,
                interest_id=i_mycology.interest_id,
                experience_level="Deep Dive",
                personal_note="Happy to help ID local woodland mushrooms.",
            ),
            UserInterest(
                user_id=maya.user_id,
                interest_id=i_cyanotype.interest_id,
                experience_level="Casual",
                personal_note="Making botanical sun prints on watercolor paper.",
            ),
            UserInterest(
                user_id=liam.user_id,
                interest_id=i_mycology.interest_id,
                experience_level="Casual",
                personal_note="Spotting fungi on morning trail runs.",
            ),
            UserInterest(
                user_id=liam.user_id,
                interest_id=i_cyanotype.interest_id,
                experience_level="Deep Dive",
                personal_note="Mixing potassium ferricyanide sensitizer from scratch.",
            ),
            # Priya & Sam populate the remaining niche interests
            UserInterest(
                user_id=priya.user_id,
                interest_id=i_translated_novellas.interest_id,
                experience_level="Deep Dive",
                personal_note="Currently reading Kobo Abe.",
            ),
            UserInterest(
                user_id=priya.user_id,
                interest_id=i_cyanotype.interest_id,
                experience_level="Curious",
                personal_note="Just bought my first UV lamp.",
            ),
            UserInterest(
                user_id=sam.user_id,
                interest_id=i_watchmaking.interest_id,
                experience_level="Deep Dive",
                personal_note="Restoring a 1968 Seiko movement.",
            ),
            UserInterest(
                user_id=sam.user_id,
                interest_id=i_field_recording.interest_id,
                experience_level="Casual",
                personal_note="Recording rain on tin roofs.",
            ),
        ]
        db.session.add_all(user_interests)

        # -------------------------------------------------------------------
        # 6. Connections (Friendships)
        # -------------------------------------------------------------------
        connections = [
            Connection(requester_id=alex.user_id,
                       addressee_id=maya.user_id, status="accepted"),
            Connection(requester_id=liam.user_id,
                       addressee_id=alex.user_id, status="accepted"),
            Connection(requester_id=priya.user_id,
                       addressee_id=alex.user_id, status="pending"),
        ]
        db.session.add_all(connections)

        # -------------------------------------------------------------------
        # 7. ChatRooms & RoomMessages
        # -------------------------------------------------------------------
        rooms = [
            ChatRoom(
                interest_id=i_mycology.interest_id,
                admin_user_id=maya.user_id,
                room_rules="Never eat wild mushrooms based solely on internet IDs!",
            ),
            ChatRoom(
                interest_id=i_cyanotype.interest_id,
                admin_user_id=liam.user_id,
                room_rules="Share your exposure times and paper types.",
            ),
            ChatRoom(
                interest_id=i_sundials.interest_id,
                admin_user_id=alex.user_id,
                room_rules="Post GPS pins and photos of historic sundials.",
            ),
            ChatRoom(
                interest_id=i_translated_novellas.interest_id,
                admin_user_id=priya.user_id,
            ),
            ChatRoom(
                interest_id=i_watchmaking.interest_id,
                admin_user_id=sam.user_id,
            ),
            ChatRoom(
                interest_id=i_field_recording.interest_id,
                admin_user_id=sam.user_id,
            ),
        ]
        db.session.add_all(rooms)
        db.session.flush()

        messages = [
            RoomMessage(
                chat_room_id=rooms[0].chat_room_id,
                user_id=maya.user_id,
                content="Welcome! Drop photos of any cool bracket fungi you spot this week.",
                is_pinned=True,
            ),
            RoomMessage(
                chat_room_id=rooms[0].chat_room_id,
                user_id=alex.user_id,
                content="Found a massive cluster of turkey tail near the river path today!",
            ),
            RoomMessage(
                chat_room_id=rooms[2].chat_room_id,
                user_id=alex.user_id,
                content="Created this room for anyone interested in medieval dial geometry.",
                is_pinned=True,
            ),
        ]
        db.session.add_all(messages)

        # -------------------------------------------------------------------
        # 8. Direct Messages
        # -------------------------------------------------------------------
        dms = [
            DirectMessage(
                sender_id=maya.user_id,
                receiver_id=alex.user_id,
                content="Hey Alex! Welcome to uni—let me know if you want to join our Sunday foraging walk.",
                is_read=False,
            ),
        ]
        db.session.add_all(dms)

        db.session.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    seed_database()
